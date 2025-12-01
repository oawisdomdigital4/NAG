#!/usr/bin/env python
"""
Seed a complete course with modules, lessons, and quiz questions
For user: oawisdomdigitalfirm@gmail.com
"""
import os
import sys
import django
from django.contrib.auth import get_user_model
from django.utils.text import slugify

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import Course, CourseModule, Lesson, QuizQuestion

User = get_user_model()

def seed_course():
    """Seed a complete course with all content types"""
    
    print("\n" + "="*60)
    print("SEEDING COMPLETE COURSE")
    print("="*60)
    
    # Get user
    user_email = 'oawisdomdigitalfirm@gmail.com'
    try:
        user = User.objects.get(email=user_email)
        print(f"\n✓ Found user: {user.email}")
    except User.DoesNotExist:
        print(f"\n✗ User {user_email} not found!")
        return False
    
    # Create course
    course_data = {
        'title': 'Python Programming Fundamentals',
        'slug': 'python-fundamentals',
        'short_description': 'Learn the basics of Python programming',
        'full_description': 'A comprehensive introduction to Python programming covering variables, data types, control flow, functions, and more.',
        'facilitator': user,
        'level': 'Beginner',
        'duration': '4 weeks',
        'format': 'Self-paced',
        'is_published': True,
        'status': 'published',
        'category': 'Technology'
    }
    
    course, created = Course.objects.get_or_create(
        slug=course_data['slug'],
        defaults=course_data
    )
    
    if created:
        print(f"\n✓ Created course: {course.title}")
    else:
        print(f"\n✓ Course already exists: {course.title}")
    
    # Module 1: Getting Started
    module1_data = {
        'course': course,
        'title': 'Module 1: Getting Started',
        'content': 'Introduction to Python and setting up your environment'
    }
    module1, _ = CourseModule.objects.get_or_create(
        course=course,
        title=module1_data['title'],
        defaults=module1_data
    )
    print(f"  ✓ Module 1: {module1.title}")
    
    # Lessons for Module 1
    lessons_m1 = [
        {
            'title': 'What is Python?',
            'lesson_type': 'video',
            'duration_minutes': 15,
            'description': 'Understanding Python and its uses',
            'video_url': 'https://www.youtube.com/watch?v=rfscVS0vtik',
            'order': 1
        },
        {
            'title': 'Installing Python',
            'lesson_type': 'article',
            'description': 'Step-by-step guide to install Python',
            'article_content': '''Python installation guide:

1. Visit python.org
2. Download the latest stable version
3. Run the installer
4. Follow the setup wizard
5. Verify installation by running: python --version

Make sure to check "Add Python to PATH" during installation.''',
            'order': 2
        },
        {
            'title': 'Your First Program',
            'lesson_type': 'quiz',
            'passing_score': 70,
            'order': 3
        }
    ]
    
    for lesson_data in lessons_m1:
        lesson, _ = Lesson.objects.get_or_create(
            module=module1,
            title=lesson_data['title'],
            defaults={**lesson_data, 'module': module1}
        )
        print(f"    ✓ Lesson: {lesson.title} ({lesson.lesson_type})")
    
    # Add quiz questions for Module 1
    quiz_lesson_m1 = Lesson.objects.get(module=module1, title='Your First Program')
    quiz_questions_m1 = [
        {
            'question_text': 'What does the print() function do?',
            'option_a': 'Sends output to a printer',
            'option_b': 'Displays text on the screen',
            'option_c': 'Saves data to a file',
            'option_d': 'Creates a new variable',
            'correct_option': 'b'
        },
        {
            'question_text': 'Which symbol is used for comments in Python?',
            'option_a': '/*',
            'option_b': '//',
            'option_c': '#',
            'option_d': '--',
            'correct_option': 'c'
        },
        {
            'question_text': 'What is the correct syntax to print "Hello"?',
            'option_a': 'print "Hello"',
            'option_b': 'print("Hello")',
            'option_c': 'echo("Hello")',
            'option_d': 'output("Hello")',
            'correct_option': 'b'
        }
    ]
    
    for q_data in quiz_questions_m1:
        QuizQuestion.objects.get_or_create(
            lesson=quiz_lesson_m1,
            question_text=q_data['question_text'],
            defaults=q_data
        )
    print(f"    ✓ Added 3 quiz questions")
    
    # Module 2: Data Types
    module2_data = {
        'course': course,
        'title': 'Module 2: Data Types and Variables',
        'content': 'Understanding Python data types: strings, integers, floats, and booleans'
    }
    module2, _ = CourseModule.objects.get_or_create(
        course=course,
        title=module2_data['title'],
        defaults=module2_data
    )
    print(f"  ✓ Module 2: {module2.title}")
    
    # Lessons for Module 2
    lessons_m2 = [
        {
            'title': 'Strings and Text',
            'lesson_type': 'video',
            'duration_minutes': 20,
            'description': 'Working with text in Python',
            'video_url': 'https://www.youtube.com/watch?v=k9TUPpGqYTo',
            'order': 1
        },
        {
            'title': 'Numbers and Math',
            'lesson_type': 'video',
            'duration_minutes': 18,
            'description': 'Integer and float operations',
            'video_url': 'https://www.youtube.com/watch?v=ohzjcVF-uzI',
            'order': 2
        },
        {
            'title': 'Data Types Quiz',
            'lesson_type': 'quiz',
            'passing_score': 70,
            'order': 3
        }
    ]
    
    for lesson_data in lessons_m2:
        lesson, _ = Lesson.objects.get_or_create(
            module=module2,
            title=lesson_data['title'],
            defaults={**lesson_data, 'module': module2}
        )
        print(f"    ✓ Lesson: {lesson.title} ({lesson.lesson_type})")
    
    # Add quiz questions for Module 2
    quiz_lesson_m2 = Lesson.objects.get(module=module2, title='Data Types Quiz')
    quiz_questions_m2 = [
        {
            'question_text': 'What is the data type of 3.14?',
            'option_a': 'int',
            'option_b': 'float',
            'option_c': 'string',
            'option_d': 'double',
            'correct_option': 'b'
        },
        {
            'question_text': 'Which operation concatenates two strings?',
            'option_a': 'String + String',
            'option_b': 'String - String',
            'option_c': 'String * String',
            'option_d': 'String / String',
            'correct_option': 'a'
        },
        {
            'question_text': 'What does 5 // 2 return?',
            'option_a': '2.5',
            'option_b': '2',
            'option_c': '3',
            'option_d': '2.0',
            'correct_option': 'b'
        }
    ]
    
    for q_data in quiz_questions_m2:
        QuizQuestion.objects.get_or_create(
            lesson=quiz_lesson_m2,
            question_text=q_data['question_text'],
            defaults=q_data
        )
    print(f"    ✓ Added 3 quiz questions")
    
    # Module 3: Control Flow
    module3_data = {
        'course': course,
        'title': 'Module 3: Control Flow',
        'content': 'Learn if statements, loops, and decision making'
    }
    module3, _ = CourseModule.objects.get_or_create(
        course=course,
        title=module3_data['title'],
        defaults=module3_data
    )
    print(f"  ✓ Module 3: {module3.title}")
    
    # Lessons for Module 3
    lessons_m3 = [
        {
            'title': 'If Statements',
            'lesson_type': 'video',
            'duration_minutes': 22,
            'description': 'Conditional logic in Python',
            'video_url': 'https://www.youtube.com/watch?v=DZwmZ8Usvnk',
            'order': 1
        },
        {
            'title': 'For and While Loops',
            'lesson_type': 'video',
            'duration_minutes': 25,
            'description': 'Repeating code with loops',
            'video_url': 'https://www.youtube.com/watch?v=beA8r1qG4ZE',
            'order': 2
        },
        {
            'title': 'Control Flow Assignment',
            'lesson_type': 'assignment',
            'estimated_hours': 2,
            'due_date': '2025-12-15',
            'description': 'Write a program using if statements and loops',
            'order': 3
        },
        {
            'title': 'Control Flow Quiz',
            'lesson_type': 'quiz',
            'passing_score': 75,
            'order': 4
        }
    ]
    
    for lesson_data in lessons_m3:
        lesson, _ = Lesson.objects.get_or_create(
            module=module3,
            title=lesson_data['title'],
            defaults={**lesson_data, 'module': module3}
        )
        print(f"    ✓ Lesson: {lesson.title} ({lesson.lesson_type})")
    
    # Add quiz questions for Module 3
    quiz_lesson_m3 = Lesson.objects.get(module=module3, title='Control Flow Quiz')
    quiz_questions_m3 = [
        {
            'question_text': 'What keyword is used for a conditional statement?',
            'option_a': 'when',
            'option_b': 'if',
            'option_c': 'check',
            'option_d': 'condition',
            'correct_option': 'b'
        },
        {
            'question_text': 'How many times does this loop run: for i in range(5)?',
            'option_a': '4',
            'option_b': '5',
            'option_c': '6',
            'option_d': 'Infinite',
            'correct_option': 'b'
        },
        {
            'question_text': 'What is the else clause used for?',
            'option_a': 'Second condition',
            'option_b': 'Executes when if is false',
            'option_c': 'Error handling',
            'option_d': 'None of the above',
            'correct_option': 'b'
        },
        {
            'question_text': 'Which loop is best for iterating over a range?',
            'option_a': 'while loop',
            'option_b': 'if loop',
            'option_c': 'for loop',
            'option_d': 'do-while loop',
            'correct_option': 'c'
        }
    ]
    
    for q_data in quiz_questions_m3:
        QuizQuestion.objects.get_or_create(
            lesson=quiz_lesson_m3,
            question_text=q_data['question_text'],
            defaults=q_data
        )
    print(f"    ✓ Added 4 quiz questions")
    
    # Create enrollment for the user
    from courses.models import Enrollment
    enrollment, created = Enrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={'progress': 0}
    )
    
    if created:
        print(f"\n✓ Enrollment created for {user.email}")
    else:
        print(f"\n✓ Enrollment already exists for {user.email}")
    
    print("\n" + "="*60)
    print("COURSE SEEDING COMPLETE!")
    print("="*60)
    print(f"\nCourse Details:")
    print(f"  Title: {course.title}")
    print(f"  Slug: {course.slug}")
    print(f"  Facilitator: {course.facilitator.email}")
    print(f"  Modules: {course.modules.count()}")
    print(f"  Total Lessons: {sum(m.lessons.count() for m in course.modules.all())}")
    print(f"  Total Quiz Questions: {QuizQuestion.objects.filter(lesson__module__course=course).count()}")
    print("\n")

if __name__ == '__main__':
    seed_course()
