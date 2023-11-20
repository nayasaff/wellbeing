from assessment.models import *


def createAppropiateQuestion(question, assessment, result):
    if question['type'] == 'matrix':
        Matrix.objects.create(id=question['id'],question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result , matrix_type=question['matrix_type'], columns=question['columns'], scores=question['scores'], options=question['options'])
    elif question['type'] == 'scale':
        Scale.objects.create(id=question['id'], question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result  , reversed=question['reversed'], options = question['options'])
    else :
        current_question = Question(id=question['id'], question_name=question['question_name'], type=question['type'], assessment=assessment, optional=True if question['optional'] == "true" else False, result=result)
        current_question.save()
        if(current_question.type == 'radio button' or current_question.type == 'checkbox' or current_question.type == 'dropdown'):
            for option in question['options']:
                Option.objects.create(question=current_question, option_name=option['option_name'], score=option['score'])
            

def geResultOfQuestion(question, assessment_id):
    results = Results.objects.filter(assessment_id = assessment_id)
    for result in results:
        if question["category"] == result.measurement:
            return result
        
def createResults(results, assessment):
    for result in results:
        new_result = Results.objects.create(measurement=result['measurement'], weight=result['weight'], assessment=assessment)
        scores = result['score']
        for score in scores:
            new_score = Score(score_name=score['score_name'], description=score['description'], guidance=score['guidance'], result=new_result, minimum_score=score['minimum_score'], maximum_score=score['maximum_score'])
            if "key_words" in score and score['key_words'] != None :
                new_score.key_words = score['key_words']
            new_score.save()

def answersExist(index, answers):
    return f"answer{index}" in answers

def handleScaleQuestion(scale_question, result, answerIndex):
    optionsLen = len(scale_question.options)
    if scale_question.reversed:
        
        return result.weight- (((answerIndex + 1) / optionsLen) * result.weight)
    else :
        return ((answerIndex + 1) / optionsLen) * result.weight
    
def handleCheckBoxQuestion(question, answers):
    results = []
    for ans in answers:
        option = Option.objects.get(question = question, option_name = ans)
        results.append(option.score)
    return results

def handleMatrixQuestion(matrix_question, answers, result):
    new_score = []
    for index,ans in enumerate(answers):
        answerIndex = matrix_question.options.index(ans)
        if matrix_question.matrix_type == "Radio Button":
            
            new_score.append(matrix_question.scores[index][answerIndex])
        elif matrix_question.matrix_type == "Checkbox":
            for ans2 in ans:
                answerIndex = matrix_question.options.index(ans2)
                new_score.append(matrix_question.scores[index][answerIndex])
        else :
            optionsLen = len(matrix_question.options)
            if matrix_question.columns[index]['reversed'] == False :
                avgScore = ((answerIndex + 1) / optionsLen) * result.weight
                new_score.append(avgScore)
            else :
                avgScore = result.weight- (((answerIndex + 1) / optionsLen) * result.weight)
                new_score.append(avgScore)
    return new_score

def calculateFinalScore(scores, user, assessment_user):
    for key, list in scores.items():
        count = 0
        for value in list :
            count += float(value)
        avgCount = count/len(list) if len(list) != 0 else 0
        assessment_user.final_score.append(avgCount)
        final_score = Score.objects.get(result__assessment_id = assessment_user.assessment_id  ,result__measurement=key, minimum_score__lte=int(avgCount), maximum_score__gte=int(avgCount))
        assessment_user.scores.add(final_score)
    assessment_user.save()

def handleDeletedData(results, question, assessment):
    existing_results = Results.objects.filter(assessment_id = assessment['id'])
    existing_question = Question.objects.filter(assessment_id = assessment['id'])
    deleted_questions = existing_question.exclude(id__in=[question['id'] for question in question])
    deleted_questions.delete()
    for result in existing_results :
        found = any(d.get("id") == result.id for d in results)
        if found:
            current_scores = Score.objects.filter(result = result)
            for score in current_scores:
                try:
                    results.index({"id": score.id})
                except :
                    score.delete()
        else :
            result.delete()

