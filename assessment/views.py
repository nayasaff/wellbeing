from django.http import JsonResponse
from lists.libraries import library
from django.views.decorators.csrf import csrf_exempt
from assessment.models import *
from users.models import *
from assessment.serializers import *
import json
from rest_framework.decorators import api_view
from django.forms.models import model_to_dict
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from django.db import transaction
from assessment.helpers import *
from users.decorators import *
import ast

@csrf_exempt
def getLibraries(request):
    libraries = Library.objects.all()
    return JsonResponse(list(libraries.values()), safe=False)

@csrf_exempt
def getLibrariesWithCategory(request):
    libraries = Library.objects.all()
    filtered_libraries = []
    for library in libraries:
        if libraries.categories['approved'] == False:
            filtered_libraries.append(library)
    return JsonResponse(list(filtered_libraries.values()), safe=False)

@api_view(['POST', 'PATCH'])
@admin_required
def editLibrary(request, libraryId):
    if request.method == 'POST':
        body = json.loads(request.body)
        if body['approved'] :
            Library.objects.filter(pk=libraryId).update(approved = body['approved'])
        else :
            Library.objects.filter(pk=libraryId).delete()
        return JsonResponse({"status": "success"}, status=200)
    elif request.method == 'PATCH' :
        body = json.loads(request.body)
        Library.objects.filter(pk=libraryId).update(library_name=body['name'], description=body['description'], categories=body['categories'], image=body['image'])
        return JsonResponse({"status": "success"}, status=200)


@api_view(['POST'])
def createLibrary(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        library_name = body['name']
        description = body['description']
        categories = body['categories']
        image = body['image']
        library = Library(library_name=library_name, description=description, categories=categories, image=image)
        library.save()
        return JsonResponse({"status": "success"}, status=200)

@csrf_exempt
def getAssessments(request):
    assessments = Assessment.objects.all()
    assessmentsSerializer = AssessmentSerializer(assessments, many=True)
    return JsonResponse(assessmentsSerializer.data, safe=False)

@api_view(['GET'])
def getAssessmentsOfCoach(request):
    assessments = Assessment.objects.filter(coach=request.user)
    assessmentsSerializer = AssessmentSerializer(assessments, many=True)
    return JsonResponse(assessmentsSerializer.data, safe=False)


@csrf_exempt
def getAssessmentById(request, id):
    assessment = Assessment.objects.get(id=id)
    questions = []
    ass_question = Question.objects.filter(assessment= assessment)
    for a_q in ass_question :
        if a_q.type == 'matrix':
            matrix_question = Matrix.objects.get(pk = a_q.id)
            questions.append(model_to_dict(matrix_question))
        elif a_q.type == 'scale':
            scale_question = Scale.objects.get(pk = a_q.id)
            questions.append(model_to_dict(scale_question))
        else : 
            serialized_question = QuestionSerializer(a_q).data
            questions.append(serialized_question)
    result = AssessmentSerializer(assessment).data
    print(result)
    result['questions'] = questions
    return JsonResponse(result, safe=False)

@csrf_exempt
def getAllCategories(request):
    libraries = Library.objects.filter(approved=True)
    result = []
    for library in libraries:
        result.append(library.library_name)
        for category in library.categories:
            if category['approved'] == True:
                result.append(category['name'])
    return JsonResponse(result, safe=False)

@csrf_exempt
def createLiberty(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        for library in body:
            library_name = library['name']
            description = library['description']
            categories = library['categories']
            image = library['image']
            library = Library(library_name=library_name, description=description, categories=categories, image=image)
            library.save()
        return JsonResponse({"status": "success"})


def analyzeScoringScheme(score, result):
    scores = Score.objects.filter(result_id = result.id)
    for level, (lower, upper) in scores.scores.items():
        if lower <= score <= upper:
            return (lower + upper) / 2
        


def tokenize(text):
    sentence = sent_tokenize(text)
    tokenized_sentence = [word_tokenize(t) for t in sentence ]
    return tokenized_sentence

def defineNegation(input):
    negation = False
    #negation_words = ["not", "no", "never", "neither", "nor", "none", "nobody", "nothing", "nowhere", "hardly", "scarcely", "barely", "doesn't", "isn’t", "wasn't", "shouldn't", "wouldn't", "couldn't", "won't", "can't", "don't"]
    for word in input:
        if re.search("(n't|not|no|never|neither|nor|none|nobody|nothing|nowhere|hardly|scarcely|barely)", word.lower() ):
            negation = True
    return negation


def analyzeOpenEndedQuestions(input, assessment_id, result_id):
    # scores = Score.objects.filter(result__id = result_id, result__assessment__id = assessment_id)
    key_words_dict = {"Introvert" : ['stay at home', 'online', 'few friends'], "Extrovert" : {'friends', 'hang out', 'party'}}
    # for score in scores:
    #     for key_word in score["key_words"]:
    #         key_words_dict[key_word] = (score["min"] + score["max"])/ 2
    scores = []

    for i in tokenize(input):
        for index,j in enumerate(i):
            print(j)
            word_exists = any(j in words for words in key_words_dict.values())
            if word_exists != False:
                negation_exists = defineNegation(i[:index])
                word_exists = (100 - word_exists) if negation_exists else word_exists
                scores.append(word_exists)
    final_score = sum(scores)
    return final_score



@api_view(['POST'])
def calculateResults(request, id) :
    with transaction.atomic():
        if request.method == 'POST':
            #TODO add kaza score example Stress Anxiety
            request_body = json.loads(request.body)
            answers = request_body["formData"]
            questions = Question.objects.filter(assessment_id = id)
            results = Results.objects.filter(assessment_id = id)
            scores = {}
            user = Users.objects.get(username = request.user)
            if(user.role.lower() == 'user') :
                new_user = User.objects.get(username = request.user)
                new_user.Total_Assessments += 1
                new_user.save()
            current_assessment = Assessment.objects.get(pk=id)
            if( current_assessment.external_link != "" ):
                print(request_body["scores"])
                assessment_user = AssessmentUser.objects.create(assessment_id = id, user = request.user, final_score= request_body["scores"]  )
                assessment_user.save()
                return JsonResponse("external link", safe=False)        
            for result_in_question in results:
                scores[result_in_question.measurement] = []
            for index, question in enumerate(questions):
                #check if the question is optional and the answer is empty
                if not answersExist(index, answers) :
                    continue
                #handle each type of question differently
                result = question.result
                if (question.type =='radio button' or question.type == 'drop down') :
                    print(answers[f"answer{index}"])
                    options = Option.objects.get(question_id = question.id, option_name = answers[f"answer{index}"])
                    scores[question.category].append(options.score)
                elif question.type == 'scale':
                    scale_question = Scale.objects.get(pk = question.id)
                    answerIndex = scale_question.options.index(answers[f"answer{index}"])
                    handleScaleQuestion(scale_question, result, answerIndex)

                elif question.type == 'checkbox':
                    scores[question.category] += handleCheckBoxQuestion(question, answers[f"answer{index}"])

                elif question.type == 'matrix':
                    matrix_question = Matrix.objects.get(pk = question.id)
                    scores[question.category] += handleMatrixQuestion(matrix_question, answers[f"answer{index}"], result)

                # elif (question.type == 'short answer' or question.type == 'long answer') :
                #     scores[question.category].append(analyzeOpenEndedQuestions(answers[f"answer{index}"]))

            assessment_user = AssessmentUser.objects.create(assessment_id = id, user = user, final_score= [] )
            calculateFinalScore(scores, user ,assessment_user)

            response = AssessmentUserSerializer(assessment_user).data
            print(response)
            return JsonResponse( response["id"] , safe=False)

    
@api_view(['GET'])
def getResults(request, id):
    assessment_user = AssessmentUser.objects.get(pk=id)
    print(assessment_user.user.username, request.user.username)
    if(assessment_user.user.username != request.user.username ):
        return JsonResponse({"message" : "You are not allowed to view this assessment"}, status=400)
    results = Results.objects.filter(assessment_id = assessment_user.assessment_id)
    final_result = []
    for res in results:
        scores = Score.objects.filter(result_id = res.id)
        final_result.append({"measurement" : res.measurement, "weight" : res.weight, "scores" : list(scores.values())})
    response = {
        "results" : final_result,
        "assessment_user" : AssessmentUserSerializer(assessment_user).data,
    }
    return JsonResponse(response, safe=False)

@api_view(['GET'])
def getAllResults(request):
    assessment_user = AssessmentUser.objects.filter(user_id=request.user.id).order_by('-date')
    allResults = AssessmentUserSerializer(assessment_user, many=True).data
    return JsonResponse(allResults, safe=False)

def getResultsOfUser(request, id):
    assessment_user = AssessmentUser.objects.filter(assessment_id=id, user_id=request.user)
    return JsonResponse(list(assessment_user.values()), safe=False)



@api_view(['POST', 'PATCH'])
def createAssessment(request):
    with transaction.atomic():
        if request.method == 'POST':
            body = json.loads(request.body)
            assessment = body['assessment']
            print(request.user)
            coach = Coach.objects.get(username = request.user)
            assessment = Assessment(title=assessment['title'], description=assessment['description'], categories=assessment['categories'], library=assessment["categories"] , coach=coach, general_description=assessment['general_description'])
            assessment.save()
            print(body)
            if "externalLink" in body:
                assessment.external_link = body['externalLink']
                assessment.scales = body['scales']
                assessment.save()
                return JsonResponse({"status": "success"}, status=200)
            results = body['results']
            questions = body['questions']
            createResults(results, assessment)
            for question in questions:
                if question['type'] != '':
                    result = geResultOfQuestion(question, assessment.id)
                    if(question['type'] == 'matrix'):
                        Matrix.objects.create(question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result , matrix_type=question['matrix_type'], columns=question['columns'], scores=question['scores'], options=question['options'])
                    elif(question['type'] == 'scale'):
                        Scale.objects.create(question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result  , reversed=question['reversed'], options = question['options'])
                    else :
                        current_question = Question(question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result)
                        current_question.save()
                        if(current_question.type == 'radio button' or current_question.type == 'checkbox' or current_question.type == 'drop down'):
                            for option in question['options']:
                                Option.objects.create(question=current_question, option_name=option['option_name'], score=option['score'])
            coach.created_assessments += 1
            coach.save()
            return JsonResponse({"status": "success"}, status=200)
        if request.method == 'PATCH' :
            body = json.loads(request.body)
            
            assessment = body['assessment']
            Assessment.objects.filter(pk = assessment['id']).update(title=assessment['title'], description=assessment['description'], categories=assessment['categories'], general_description=assessment['general_description'])
            if "externalLink" in body:
                Assessment.objects.filter(pk = assessment['id']).update(external_link = body['externalLink'], scales = body['scales'])
                return JsonResponse({"status": "success"}, status=200)
            handleDeletedData(body['results'], body['questions'], body['assessment'])
            for question in body['questions']:
                result = geResultOfQuestion(question, assessment['id'])
                if "id" in question:
                    current_question = Question.objects.get(pk=question['id'])
                    if(current_question.type == 'matrix'):
                        if question['type'] == 'matrix':
                            print(current_question.id)
                            Matrix.objects.filter(pk=current_question.id).update(question_name=question['question_name'], type=question['type'],  optional=True if question['optional'] == "true" else False, result=result,matrix_type=question['matrix_type'], columns=question['columns'], options=question['options'])
                        else :
                            Matrix.objects.filter(pk=current_question.id).delete()
                            createAppropiateQuestion(question, assessment, result)
                    elif(current_question.type == 'scale'):
                        if question['type'] == 'scale':
                            Scale.objects.filter(pk=question['id']).update(question_name=question['question_name'], type=question['type'], optional=True if question['optional'] == "true" else False, result=result,reversed=question['reversed'], options = question['options'])
                        else :
                            Scale.objects.filter(pk=question['id']).delete()
                            createAppropiateQuestion(question, assessment, result)
                    else :
                        if question['type'] == 'matrix' or question['type'] == 'scale':
                            createAppropiateQuestion(question, assessment, result)
                        else :
                            Question.objects.filter(pk=question['id']).update(question_name=question['question_name'], type=question['type'], optional=True if question['optional'] == "true" else False, result=result)
                            if(current_question.type == 'radio button' or current_question.type == 'checkbox' or current_question.type == 'drop down'):
                                for option in question['options']:
                                    if "id" in option:
                                        Option.objects.filter(pk=option['id']).update(option_name=option['option_name'], score=option['score'])
                                    else :
                                        Option.objects.create(question=current_question, option_name=option['option_name'], score=option['score'])
                else :
                    createAppropiateQuestion(question, assessment, result)
            for result in body['results']:
                if "id" in result:
                    Results.objects.filter(pk=result['id']).update(measurement=result['measurement'],weight=result['weight'])
                    for score in result['score']:
                        if "id" in score:
                            Score.objects.filter(id=score['id']).update(score_name = score['score_name'], description = score['description'], guidance = score['guidance'], minimum_score = score['minimum_score'], maximum_score = score['maximum_score'])
                        else :
                            Score.objects.create(score_name = score['score_name'], description = score['description'], guidance = score['guidance'], minimum_score = score['minimum_score'], maximum_score = score['maximum_score'])
                        if "key_words" in score and score['key_words'] != None :
                            Score.objects.filter(pk=score['id']).update(key_words = score['key_words'])
                else :
                    createResults(body['results'], assessment)

            return JsonResponse({"status": "success"}, status=200)
    

    
@csrf_exempt
def processFile(request):
    if request.method == 'POST':
        try:
            file = request.FILES
            body = request.POST
            file_name = file.get("file")
            #convert scale to list
            scale = body.get("scale")
            scale = ast.literal_eval(scale)
            print(scale)
            df = pd.read_csv(file_name)
            df.columns = df.columns.str.lower()
            expected_columns = ["question name","options"]
            expected_types = ["scale", "radio button", "checkbox" ,"short answer", "long answer", "drop down", "matrix"]
            values_not_found = [item for item in expected_columns if item not in df.columns ]
            if values_not_found:
                return JsonResponse(f'Plase Make the csv file contains "{values_not_found[0]}" column', safe=False, status=400)
            questions = []
            for index,row in df.iterrows():
                if "type" in df and row["type"] not in expected_types:
                    expected_types_str = ", ".join(expected_types)
                    print(row["type"] not in expected_types)
                    return JsonResponse(f'Plase Make the csv file contains "{expected_types_str}" as type of question', safe=False, status=400)
                if "scale" in df and row["scale"] not in scale:
                    scale_str = ", ".join(scale)
                    return JsonResponse(f'Plase make you include one of the scale names you chose "{scale_str}"', safe=False, status=400)
                if "optional" in df and row["optional"].lower() not in ["yes", "no"]:
                    return JsonResponse('Plase make sure the optional columns contains "yes" or "no" values', safe=False, status=400)
            
                options_list = row["options"].split(",")
                if row["type"] == 'radio button' or row["type"] == 'checkbox' or row["type"] == 'drop down':
                    current_question = {"question_name" : row["question name"], "options" : [{ "score": "", "option_name": option } for option in options_list] }
                else :
                    current_question = {"question_name" : row["question name"], "options" : options_list}
                if "type" in df:
                    current_question["type"] = row["type"].lower()
                if "optional" in df:
                    current_question["optional"] = True if row["optional"].lower() == "yes" else False
                if "scale" in df:
                    current_question["scale"] = row["scale"]
                questions.append(current_question) 
            return JsonResponse(questions, safe=False)
        except Exception as e: 
            return JsonResponse(str(e), safe=False, status=400)
        
@csrf_exempt
def test(request):
    if request.method == 'POST':
        response = "My social life is incredibly active and vibrant. I have a wide circle of friends and participate in various social activities, parties, and events. I enjoy meeting new people and exploring different social scenes."
        data = analyzeOpenEndedQuestions(response, 1, 0)
        return JsonResponse(data, safe=False)
    
@api_view(['PATCH'])
def addCategory(request, libraryId):
    try:
        if request.method == 'PATCH':
            body = json.loads(request.body)
            library = Library.objects.get(pk=libraryId)
            if request.user.role.lower() == 'coach' :
                library.categories.append({"name" : body, "approved" : False})
            elif request.user.role.lower() == 'admin' :
                library.categories.append({"name" : body, "approved" : True})
            library.save()
            return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        return JsonResponse({"status": str(e)}, status=400)

