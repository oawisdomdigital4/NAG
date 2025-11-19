"""
Auto-grading system for quizzes and assignments
"""
from .models import QuizSubmission, QuizQuestion, AssignmentSubmission, Enrollment, Lesson
from datetime import datetime, timedelta
from django.utils import timezone
import re


class QuizAutoGrader:
    """Auto-grader for objective quiz questions"""
    
    @staticmethod
    def grade_quiz(submission: QuizSubmission) -> int:
        """
        Grade a quiz submission by comparing answers to correct options.
        
        Args:
            submission: QuizSubmission instance
            
        Returns:
            int: Score percentage (0-100)
        """
        answers = submission.answers  # {question_id: selected_option}
        questions = submission.lesson.questions.all()
        
        if not questions.exists():
            return 0
        
        correct_count = 0
        question_scores = {}
        
        for question in questions:
            selected_option = answers.get(str(question.id))
            is_correct = selected_option and selected_option.lower() == question.correct_option.lower()
            
            if is_correct:
                correct_count += 1
                question_scores[question.id] = 100
            else:
                question_scores[question.id] = 0
        
        # Calculate percentage
        score = (correct_count / questions.count()) * 100
        submission.score = int(score)
        submission.graded = True
        submission.question_scores = question_scores
        submission.save(update_fields=['score', 'graded', 'question_scores'])
        
        return submission.score
    
    @staticmethod
    def passes_quiz(submission: QuizSubmission) -> bool:
        """Check if submission passes based on lesson's passing_score"""
        passing_score = submission.lesson.passing_score or 70
        return submission.score >= passing_score
    
    @staticmethod
    def get_quiz_feedback(submission: QuizSubmission) -> dict:
        """Generate detailed feedback for quiz submission"""
        questions = submission.lesson.questions.all()
        feedback = []
        
        for question in questions:
            selected_option = submission.answers.get(str(question.id))
            is_correct = selected_option and selected_option.lower() == question.correct_option.lower()
            
            feedback.append({
                'question_id': question.id,
                'question_text': question.text,
                'selected_answer': selected_option,
                'correct_answer': question.correct_option,
                'is_correct': is_correct,
                'explanation': getattr(question, 'explanation', 'Review the course materials for more details.')
            })
        
        return {
            'score': submission.score,
            'passed': QuizAutoGrader.passes_quiz(submission),
            'total_questions': len(feedback),
            'correct_answers': sum(1 for f in feedback if f['is_correct']),
            'feedback': feedback
        }


class AssignmentAutoGrader:
    """Auto-grader for assignments with content analysis"""
    
    @staticmethod
    def analyze_content_quality(content: str) -> dict:
        """Analyze quality metrics of submitted content"""
        if not content or not content.strip():
            return {
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'has_citations': False,
                'quality_score': 0
            }
        
        # Remove extra whitespace
        clean_content = ' '.join(content.split())
        
        # Count metrics
        words = clean_content.split()
        sentences = re.split(r'[.!?]+', clean_content)
        paragraphs = content.split('\n\n')
        
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Check for citations
        has_citations = bool(re.search(r'\([Cc]ited|"[^"]*"\s*(?:\(|--)', content))
        
        # Calculate quality score based on content
        quality_score = 50  # Base score
        
        # Word count bonus (50-300 words = quality baseline)
        if 50 <= word_count <= 300:
            quality_score += 20
        elif word_count > 300:
            quality_score += 15
        
        # Sentence variety
        if sentence_count > 3:
            quality_score += 15
        
        # Paragraph structure
        if paragraph_count > 2:
            quality_score += 10
        
        # Citation indicator
        if has_citations:
            quality_score += 10
        
        quality_score = min(100, quality_score)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'has_citations': has_citations,
            'quality_score': quality_score
        }
    
    @staticmethod
    def grade_assignment(submission: AssignmentSubmission, keywords: list = None) -> int:
        """
        Grade an assignment based on content analysis.
        
        Args:
            submission: AssignmentSubmission instance
            keywords: Optional list of keywords to check for
            
        Returns:
            int: Score (0-100)
        """
        if not submission.content or submission.content.strip() == '':
            submission.score = 0
            submission.graded = True
            submission.save(update_fields=['score', 'graded'])
            return 0
        
        # Analyze content quality
        quality = AssignmentAutoGrader.analyze_content_quality(submission.content)
        base_score = quality['quality_score']
        
        # Apply keyword analysis if provided
        if keywords:
            content_lower = submission.content.lower()
            found_keywords = sum(1 for kw in keywords if kw.lower() in content_lower)
            keyword_score = (found_keywords / len(keywords)) * 100 if keywords else 100
            base_score = int(base_score * 0.6 + keyword_score * 0.4)
        
        submission.score = min(100, base_score)
        submission.graded = True
        submission.auto_graded = True
        submission.save(update_fields=['score', 'graded', 'auto_graded'])
        
        return submission.score
    
    @staticmethod
    def check_plagiarism(submission: AssignmentSubmission) -> dict:
        """Basic plagiarism detection (checks for common patterns)"""
        content = submission.content.lower()
        
        suspicious_patterns = {
            'excessive_quoting': len(re.findall(r'"[^"]{50,}"', content)) > 5,
            'ai_patterns': bool(re.search(r'\b(as an ai|i am an ai|as a language model)\b', content)),
            'repeated_phrases': len(set(re.findall(r'\b\w+\b', content))) < len(content.split()) * 0.3
        }
        
        return {
            'submission_id': submission.id,
            'suspicious': any(suspicious_patterns.values()),
            'patterns_found': suspicious_patterns,
            'confidence': 'low'  # Could be enhanced with external plagiarism API
        }
    
    @staticmethod
    def manual_grade_assignment(submission: AssignmentSubmission, score: int, feedback: str = None) -> None:
        """
        Manually grade an assignment (for instructor override).
        
        Args:
            submission: AssignmentSubmission instance
            score: Score to assign (0-100)
            feedback: Optional instructor feedback
        """
        submission.score = max(0, min(100, score))  # Clamp between 0-100
        submission.graded = True
        submission.auto_graded = False
        
        if feedback:
            submission.feedback = feedback
        
        submission.save(update_fields=['score', 'graded', 'auto_graded', 'feedback'])
    
    @staticmethod
    def get_assignment_feedback(submission: AssignmentSubmission) -> dict:
        """Generate detailed feedback for assignment submission"""
        quality = AssignmentAutoGrader.analyze_content_quality(submission.content)
        plagiarism = AssignmentAutoGrader.check_plagiarism(submission)
        
        feedback_items = []
        
        # Word count feedback
        if quality['word_count'] < 50:
            feedback_items.append({
                'type': 'warning',
                'message': 'Content is quite brief. Consider expanding your response with more detail.'
            })
        elif quality['word_count'] > 500:
            feedback_items.append({
                'type': 'info',
                'message': 'Good length. Ensure all content is relevant and not repetitive.'
            })
        
        # Structure feedback
        if quality['paragraph_count'] < 2:
            feedback_items.append({
                'type': 'suggestion',
                'message': 'Organize your response into multiple paragraphs for better readability.'
            })
        
        # Citation feedback
        if not quality['has_citations']:
            feedback_items.append({
                'type': 'suggestion',
                'message': 'Consider including citations for external sources.'
            })
        
        return {
            'submission_id': submission.id,
            'score': submission.score,
            'quality_metrics': quality,
            'plagiarism_check': plagiarism,
            'feedback': feedback_items,
            'submitted_at': submission.submitted_at,
            'graded_by': 'Automated Grading System' if submission.auto_graded else 'Instructor'
        }


class ProgressTracker:
    """Track student progress through course lessons"""
    
    @staticmethod
    def calculate_lesson_progress(enrollment: Enrollment) -> dict:
        """
        Calculate progress for all lessons in enrolled course.
        
        Returns:
            dict: {
                'total_lessons': int,
                'completed_lessons': int,
                'quiz_average': float,
                'assignment_average': float,
                'overall_progress': int (0-100)
            }
        """
        course = enrollment.course
        modules = course.modules.all()
        
        all_lessons = []
        for module in modules:
            all_lessons.extend(module.lessons.all())
        
        if not all_lessons:
            return {
                'total_lessons': 0,
                'completed_lessons': 0,
                'quiz_average': 0,
                'assignment_average': 0,
                'overall_progress': 0
            }
        
        # Check quiz submissions
        quiz_submissions = QuizSubmission.objects.filter(
            enrollment=enrollment,
            graded=True
        )
        quiz_scores = [qs.score for qs in quiz_submissions]
        quiz_average = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        # Check assignment submissions
        assignment_submissions = AssignmentSubmission.objects.filter(
            enrollment=enrollment,
            graded=True
        )
        assignment_scores = [ass.score for ass in assignment_submissions]
        assignment_average = sum(assignment_scores) / len(assignment_scores) if assignment_scores else 0
        
        # Count completed lessons (has both quiz and assignment completed or just video/article)
        completed = len(quiz_submissions) + len(assignment_submissions)
        
        # Calculate overall progress
        overall_progress = int((completed / len(all_lessons)) * 100) if all_lessons else 0
        
        return {
            'total_lessons': len(all_lessons),
            'completed_lessons': completed,
            'quiz_average': round(quiz_average, 2),
            'assignment_average': round(assignment_average, 2),
            'overall_progress': overall_progress
        }
    
    @staticmethod
    def get_student_report(enrollment: Enrollment) -> dict:
        """
        Generate comprehensive progress report for a student.
        
        Returns:
            dict with detailed progress, scores, and recommendations
        """
        progress = ProgressTracker.calculate_lesson_progress(enrollment)
        
        quiz_subs = QuizSubmission.objects.filter(enrollment=enrollment).order_by('-submitted_at')
        assignment_subs = AssignmentSubmission.objects.filter(enrollment=enrollment).order_by('-submitted_at')
        
        # Generate recommendations
        recommendations = []
        if progress['quiz_average'] < 70:
            recommendations.append('Review quiz materials - scores below passing threshold')
        if progress['assignment_average'] < 80:
            recommendations.append('Focus on assignment quality - try to improve content depth')
        if progress['overall_progress'] < 50:
            recommendations.append('Accelerate course progress - you\'re behind pace')
        
        if not recommendations:
            recommendations.append('Great progress! Keep up the momentum')
        
        return {
            'enrollment_id': enrollment.id,
            'student_name': enrollment.user.get_full_name(),
            'course_title': enrollment.course.title,
            'enrolled_at': enrollment.enrolled_at,
            'progress': progress,
            'recent_quizzes': [
                {
                    'lesson_title': qs.lesson.title,
                    'score': qs.score,
                    'submitted_at': qs.submitted_at,
                    'passed': qs.score >= (qs.lesson.passing_score or 70)
                }
                for qs in quiz_subs[:5]
            ],
            'recent_assignments': [
                {
                    'lesson_title': ass.lesson.title,
                    'score': ass.score,
                    'submitted_at': ass.submitted_at,
                    'graded_by': 'Auto-grading' if ass.auto_graded else 'Instructor'
                }
                for ass in assignment_subs[:5]
            ],
            'recommendations': recommendations
        }
    
    @staticmethod
    def calculate_learning_streak(enrollment: Enrollment) -> dict:
        """Calculate student's learning streak for a course"""
        today = datetime.now(timezone.utc).date()
        current_streak = 0
        max_streak = 0
        streak_broken_date = None
        
        # Get submission dates
        quiz_dates = QuizSubmission.objects.filter(
            enrollment=enrollment,
            submitted_at__gte=datetime.now(timezone.utc) - timedelta(days=30)
        ).values_list('submitted_at', flat=True)
        
        assignment_dates = AssignmentSubmission.objects.filter(
            enrollment=enrollment,
            submitted_at__gte=datetime.now(timezone.utc) - timedelta(days=30)
        ).values_list('submitted_at', flat=True)
        
        # Combine dates
        activity_dates = set()
        for date in list(quiz_dates) + list(assignment_dates):
            activity_dates.add(date.date())
        
        # Calculate streak
        check_date = today
        while check_date >= (today - timedelta(days=30)):
            if check_date in activity_dates:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                if current_streak > 0:
                    streak_broken_date = check_date + timedelta(days=1)
                current_streak = 0
            
            check_date -= timedelta(days=1)
        
        return {
            'enrollment_id': enrollment.id,
            'current_streak_days': current_streak,
            'max_streak_days': max_streak,
            'streak_broken_date': streak_broken_date,
            'total_active_days_30d': len(activity_dates)
        }
    
    @staticmethod
    def predict_course_completion(enrollment: Enrollment) -> dict:
        """Predict likelihood of course completion and time to completion"""
        all_lessons = Lesson.objects.filter(course=enrollment.course)
        total_lessons = all_lessons.count()
        
        # Calculate progress
        completed_items = QuizSubmission.objects.filter(
            enrollment=enrollment, graded=True
        ).count() + AssignmentSubmission.objects.filter(
            enrollment=enrollment, graded=True
        ).count()
        
        progress_rate = (completed_items / (total_lessons * 2) * 100) if total_lessons > 0 else 0
        
        # Time-based prediction
        days_in_course = (datetime.now(timezone.utc) - enrollment.enrolled_at).days
        course_duration = getattr(enrollment.course, 'duration_days', 30)
        time_progress = (days_in_course / course_duration * 100) if course_duration > 0 else 0
        
        # Predict completion
        if progress_rate >= time_progress:
            prediction = 'on_track'
            confidence = min(95, 70 + (progress_rate - time_progress) / 2)
        elif progress_rate >= time_progress * 0.7:
            prediction = 'achievable'
            confidence = 75
        else:
            prediction = 'at_risk'
            confidence = 65
        
        # Estimate time to completion
        if progress_rate > 0 and progress_rate < 100:
            days_per_percent = days_in_course / progress_rate
            estimated_days_remaining = days_per_percent * (100 - progress_rate)
        else:
            estimated_days_remaining = course_duration - days_in_course
        
        return {
            'enrollment_id': enrollment.id,
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'progress_rate': round(progress_rate, 2),
            'time_progress': round(time_progress, 2),
            'estimated_days_remaining': max(0, round(estimated_days_remaining, 2)),
            'course_duration_days': course_duration,
            'days_elapsed': days_in_course
        }
    
    @staticmethod
    def get_performance_insights(enrollment: Enrollment) -> dict:
        """Generate detailed performance insights with actionable recommendations"""
        progress = ProgressTracker.calculate_lesson_progress(enrollment)
        streak = ProgressTracker.calculate_learning_streak(enrollment)
        completion = ProgressTracker.predict_course_completion(enrollment)
        
        # Analyze patterns
        quiz_trend = 'improving' if progress['quiz_average'] > 75 else 'needs_work'
        assignment_trend = 'strong' if progress['assignment_average'] > 80 else 'variable'
        
        # Generate insights
        insights = []
        if streak['current_streak_days'] > 5:
            insights.append({'type': 'positive', 'message': f'Great engagement! You\'ve completed work {streak["current_streak_days"]} days in a row.'})
        
        if progress['quiz_average'] < 70 and progress['assignment_average'] > 80:
            insights.append({'type': 'suggestion', 'message': 'Your assignments are strong, but quiz scores suggest areas to strengthen conceptual understanding.'})
        
        if completion['prediction'] == 'at_risk':
            insights.append({'type': 'warning', 'message': f'At current pace, course completion may take ~{int(completion["estimated_days_remaining"])} more days.'})
        
        if not insights:
            insights.append({'type': 'positive', 'message': 'You\'re performing well overall. Keep maintaining your current pace!'})
        
        return {
            'enrollment_id': enrollment.id,
            'overall_score': round((progress['quiz_average'] * 0.4 + progress['assignment_average'] * 0.6), 2),
            'progress': progress,
            'streak': streak,
            'completion_prediction': completion,
            'insights': insights,
            'generated_at': datetime.now(timezone.utc)
        }
