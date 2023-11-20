from django.urls import path
from assessment import views

urlpatterns = [
    path('getLibraries/', views.getLibraries, name='getLibraries'),
    path("getAssessments/", views.getAssessments, name="getAssessments"),
    path('createAssessment/', views.createAssessment, name='createAssessment'),
    path("getAssessmentById/<int:id>/", views.getAssessmentById, name="getAssessmentById"),
    path("calculateResults/<int:id>", views.calculateResults, name="calculateResults"),
    path("getAllCategories/", views.getAllCategories, name="getAllCategories"),
    path("createLiberty/", views.createLiberty, name="createLiberty"),
    path('processFile/', views.processFile, name='processFile'),
    path('getResults/<int:id>', views.getResults, name='getResults'),
    path("getAllResults/", views.getAllResults, name="getAllResults"),
    path("createLibrary/", views.createLibrary, name="createLibrary"),
    path("test/", views.test, name="test"),
    path("getAssessmentsOfCoach/", views.getAssessmentsOfCoach, name="getAssessmentsOfCoach"),
    path("editLibrary/<int:libraryId>", views.editLibrary, name="editLibrary"),
    path("addCategory/<int:libraryId>", views.addCategory, name="addCategory"),
    path("getLibrariesWithCategory/", views.getLibrariesWithCategory, name="getLibrariesWithCategory"),
]