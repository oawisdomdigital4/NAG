#!/usr/bin/env python
"""
Test script to verify quiz submission functionality
"""
import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from courses.models import Course, CourseModule, Lesson, QuizQuestion, QuizSubmission, Enrollment
from courses.serializers import QuizQuestionSerializer

User = get_user_model()

def test_quiz_submission():
    """Test the complete quiz submission flow"""
    print("\n" + "="*60)
    print("TESTING QUIZ SUBMISSION FLOW")
    print("="*60)
    
    # Create test data
    print("\n1. Creating test data...")
    
    # Create users
    facilitator = User.objects.create_user(
        email='facilitator@test.com',
        password='test123',
        full_name='Test Facilitator'
    )
    student = User.objects.create_user(
        email='student@test.com',
        password='test123',
        full_name='Test Student'
    )
    print(f"   ✓ Created facilitator: {facilitator.email}")
    print(f"   ✓ Created student: {student.email}")
    
    # Create course
    course = Course.objects.create(
        title='Test Course',
        slug='test-course',
        description='Test course for quiz',
        short_description='Test',
        facilitator=facilitator,
        level='Beginner',
        duration='2 hours'
    )
    print(f"   ✓ Created course: {course.title}")
    
    # Create module
    module = CourseModule.objects.create(
        course=course,
        title='Test Module',
        description='Test Module'
    )
    print(f"   ✓ Created module: {module.title}")
    
    # Create quiz lesson
    quiz_lesson = Lesson.objects.create(
        module=module,
        title='Test Quiz',
        lesson_type='quiz',
        passing_score=70,
        order=1
    )
    print(f"   ✓ Created quiz lesson: {quiz_lesson.title}")
    
    # Create quiz questions
    questions_data = [
        {
            'question_text': 'What is 2+2?',
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_option': 'b'
        },
        {
            'question_text': 'What is the capital of France?',
            'option_a': 'London',
            'option_b': 'Berlin',
            'option_c': 'Paris',
            'option_d': 'Madrid',
            'correct_option': 'c'
        },
        {
            'question_text': 'What is 10/2?',
            'option_a': '5',
            'option_b': '3',
            'option_c': '7',
            'option_d': '2',
            'correct_option': 'a'
        }
    ]
    
    questions = []
    for q_data in questions_data:
        q = QuizQuestion.objects.create(
            lesson=quiz_lesson,
            **q_data
        )
        questions.append(q)
        print(f"   ✓ Created question: {q.question_text}")
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        user=student,
        course=course,
        status='active'
    )
    print(f"   ✓ Created enrollment: {student.email} -> {course.title}")
    
    print("\n2. Testing quiz submission...")
    
    # Create API client
    client = APIClient()
    
    # Get student token
    token, created = Token.objects.get_or_create(user=student)
    print(f"   ✓ Got student token: {token.key[:20]}...")
    
    # Authenticate as student
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    # Test getting questions
    print("\n3. Getting quiz questions...")
    response = client.post(f'/api/courses/lessons/{quiz_lesson.id}/get-questions/')
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {data.get('total_questions')} questions")
    
    # Test submitting answers
    print("\n4. Submitting quiz answers...")
    answers = {
        str(questions[0].id): 'b',  # Correct
        str(questions[1].id): 'c',  # Correct
        str(questions[2].id): 'b',  # Incorrect (should be 'a')
    }
    
    print(f"   Submitting answers: {answers}")
    response = client.post(
        f'/api/courses/lessons/{quiz_lesson.id}/submit-quiz/',
        {'answers': answers},
        format='json'
    )
    
    print(f"   Status: {response.status_code}")
    response_data = response.json()
    print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 201:
        print(f"\n   ✓ Quiz submitted successfully!")
        print(f"   ✓ Score: {response_data.get('score')}%")
        print(f"   ✓ Correct: {response_data.get('correct_answers')}/{response_data.get('total_questions')}")
        print(f"   ✓ Passing: {response_data.get('is_passing')}")
        
        # Check submission was saved
        submission = QuizSubmission.objects.get(id=response_data.get('submission_id'))
        print(f"   ✓ Submission saved to database with ID: {submission.id}")
        print(f"   ✓ Submission score: {submission.score}")
        print(f"   ✓ Submission answers: {submission.answers}")
    else:
        print(f"\n   ✗ Quiz submission failed!")
        print(f"   Error: {response_data}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    test_quiz_submission()
