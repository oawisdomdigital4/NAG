"""
Quiz Retry Management System
Handles quiz retakes with configurable rules and improved tracking
"""

from django.utils import timezone
from django.db.models import Q, Avg, Max
from datetime import timedelta
from .models import QuizSubmission, Lesson, Enrollment


class QuizRetryManager:
    """Manage quiz retakes with configurable policies"""
    
    # Default retry policies
    DEFAULT_POLICIES = {
        'max_attempts': 3,
        'min_wait_hours': 24,
        'require_passing_first': False,
        'track_best_score': True,
        'improvement_bonus': False
    }
    
    @staticmethod
    def can_retake(enrollment: Enrollment, lesson: Lesson, policy: dict = None) -> dict:
        """
        Check if student can retake a quiz.
        
        Returns:
            dict with can_retake boolean and reason
        """
        if policy is None:
            policy = QuizRetryManager.DEFAULT_POLICIES
        
        # Get quiz submissions for this enrollment and lesson
        submissions = QuizSubmission.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
            graded=True
        ).order_by('-submitted_at')
        
        attempt_count = submissions.count()
        max_attempts = policy.get('max_attempts', 3)
        
        # Check max attempts
        if attempt_count >= max_attempts:
            return {
                'can_retake': False,
                'reason': f'Maximum {max_attempts} attempts reached',
                'attempt_count': attempt_count,
                'max_attempts': max_attempts
            }
        
        # Check time elapsed since last attempt
        if submissions.exists():
            last_submission = submissions.first()
            min_wait = policy.get('min_wait_hours', 24)
            time_elapsed = timezone.now() - last_submission.submitted_at
            min_wait_delta = timedelta(hours=min_wait)
            
            if time_elapsed < min_wait_delta:
                hours_remaining = (min_wait_delta - time_elapsed).total_seconds() / 3600
                return {
                    'can_retake': False,
                    'reason': f'Must wait {min_wait} hours between attempts',
                    'hours_remaining': round(hours_remaining, 1),
                    'last_attempt': last_submission.submitted_at
                }
            
            # Check if previous attempt passed (if required)
            if policy.get('require_passing_first', False):
                if not QuizRetryManager.is_passing_score(
                    last_submission.score, lesson.passing_score or 70
                ):
                    return {
                        'can_retake': False,
                        'reason': 'Must achieve passing score first',
                        'last_score': last_submission.score,
                        'passing_score': lesson.passing_score or 70
                    }
        
        return {
            'can_retake': True,
            'reason': 'Eligible for retake',
            'attempt_count': attempt_count,
            'max_attempts': max_attempts,
            'attempts_remaining': max_attempts - attempt_count
        }
    
    @staticmethod
    def is_passing_score(score: int, passing_threshold: int = 70) -> bool:
        """Check if score meets passing threshold"""
        return score >= passing_threshold
    
    @staticmethod
    def get_quiz_history(enrollment: Enrollment, lesson: Lesson) -> dict:
        """Get complete quiz attempt history with analytics"""
        submissions = QuizSubmission.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
            graded=True
        ).order_by('submitted_at')
        
        if not submissions.exists():
            return {
                'attempt_count': 0,
                'attempts': [],
                'statistics': {}
            }
        
        attempts = []
        scores = []
        
        for idx, submission in enumerate(submissions, 1):
            passing = QuizRetryManager.is_passing_score(
                submission.score, lesson.passing_score or 70
            )
            attempts.append({
                'attempt_number': idx,
                'score': submission.score,
                'submitted_at': submission.submitted_at,
                'passing': passing,
                'timestamp': submission.submitted_at.isoformat()
            })
            scores.append(submission.score)
        
        # Calculate statistics
        score_trend = 'improving' if len(scores) > 1 and scores[-1] > scores[0] else \
                     'declining' if len(scores) > 1 and scores[-1] < scores[0] else 'stable'
        
        stats = {
            'total_attempts': len(scores),
            'best_score': max(scores),
            'worst_score': min(scores),
            'average_score': sum(scores) / len(scores),
            'last_score': scores[-1],
            'improvement_from_first': scores[-1] - scores[0],
            'score_trend': score_trend,
            'passing_attempts': sum(1 for s in scores if s >= (lesson.passing_score or 70)),
            'first_attempt_passed': QuizRetryManager.is_passing_score(scores[0], lesson.passing_score or 70)
        }
        
        return {
            'attempt_count': len(attempts),
            'attempts': attempts,
            'statistics': stats
        }
    
    @staticmethod
    def record_quiz_retake(enrollment: Enrollment, lesson: Lesson, 
                          score: int, answers: dict, policy: dict = None) -> dict:
        """
        Record a new quiz retake attempt.
        
        Returns:
            dict with submission data and retry status
        """
        if policy is None:
            policy = QuizRetryManager.DEFAULT_POLICIES
        
        # Check if retake is allowed
        can_retake_info = QuizRetryManager.can_retake(enrollment, lesson, policy)
        
        if not can_retake_info['can_retake']:
            return {
                'success': False,
                'reason': can_retake_info['reason'],
                'submission': None
            }
        
        # Create new submission
        submission = QuizSubmission.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            score=score,
            answers=answers,
            graded=True
        )
        
        # Get history for context
        history = QuizRetryManager.get_quiz_history(enrollment, lesson)
        
        # Calculate improvement bonus if applicable
        bonus = 0
        if policy.get('improvement_bonus', False) and history['attempt_count'] > 1:
            prev_best = history['statistics']['best_score']
            if score > prev_best:
                improvement = score - prev_best
                bonus = min(5, improvement // 10)  # Max 5 point bonus
                score_with_bonus = min(100, score + bonus)
            else:
                score_with_bonus = score
        else:
            score_with_bonus = score
        
        return {
            'success': True,
            'reason': 'Retake recorded successfully',
            'submission': {
                'id': submission.id,
                'score': score,
                'score_with_bonus': score_with_bonus,
                'improvement_bonus': bonus,
                'submitted_at': submission.submitted_at,
                'attempt_number': history['attempt_count']
            },
            'history': history
        }
    
    @staticmethod
    def get_best_attempt(enrollment: Enrollment, lesson: Lesson) -> dict:
        """Get student's best quiz attempt"""
        submissions = QuizSubmission.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
            graded=True
        ).order_by('-score', '-submitted_at')
        
        if not submissions.exists():
            return {'found': False, 'submission': None}
        
        best = submissions.first()
        return {
            'found': True,
            'submission': {
                'id': best.id,
                'score': best.score,
                'submitted_at': best.submitted_at,
                'answers': best.answers
            }
        }
    
    @staticmethod
    def get_average_attempt(enrollment: Enrollment, lesson: Lesson) -> dict:
        """Calculate and get the attempt at average score"""
        submissions = QuizSubmission.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
            graded=True
        )
        
        if not submissions.exists():
            return {'found': False, 'average_score': 0}
        
        avg_score = submissions.aggregate(avg=Avg('score'))['avg'] or 0
        
        # Find closest submission to average
        closest_submission = min(
            submissions,
            key=lambda s: abs(s.score - avg_score)
        )
        
        return {
            'found': True,
            'average_score': round(avg_score, 2),
            'submission': {
                'id': closest_submission.id,
                'score': closest_submission.score,
                'submitted_at': closest_submission.submitted_at
            }
        }
    
    @staticmethod
    def get_retry_recommendations(enrollment: Enrollment, lesson: Lesson) -> dict:
        """Generate recommendations for quiz improvement"""
        history = QuizRetryManager.get_quiz_history(enrollment, lesson)
        
        if history['attempt_count'] == 0:
            return {
                'recommendations': ['Take the quiz to assess your understanding']
            }
        
        stats = history['statistics']
        recommendations = []
        
        # Analyze performance
        if stats['last_score'] >= (lesson.passing_score or 70):
            if stats['first_attempt_passed']:
                recommendations.append('Excellent! You passed on your first attempt.')
            else:
                recommendations.append(f'Great improvement! You\'ve improved {stats["improvement_from_first"]} points.')
        else:
            if stats['score_trend'] == 'declining':
                recommendations.append('Review the lesson materials - your scores are declining.')
            elif stats['score_trend'] == 'improving':
                recommendations.append('Keep practicing - you\'re showing improvement!')
            else:
                recommendations.append(f'You\'re {lesson.passing_score - stats["last_score"] or 70} points away from passing.')
        
        # Check attempt count
        if stats['total_attempts'] >= 2:
            recommendations.append(f'Current performance: {stats["average_score"]:.0f}% average, '
                                 f'{stats["best_score"]}% best attempt')
        
        return {
            'recommendations': recommendations,
            'statistics': stats
        }
