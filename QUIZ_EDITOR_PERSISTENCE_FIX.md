# Quiz Question Editor Form Persistence Fix

## Issue
When editing quiz questions in the quiz editor form, the "correct answer" checkbox selection (and entire form state) was not persisting when the page was refreshed.

## Root Cause
The `QuizQuestionEditor` component used only React state (via props) to manage form data, with no persistence mechanism. When the browser refreshed, all component state was lost, even though the data was potentially being loaded from the API.

## Solution Implemented
Added dual-layer persistence to `QuizQuestionEditor.tsx`:

### 1. **localStorage Persistence**
- Questions are automatically saved to `localStorage` with key `quiz_questions_{lessonId}`
- Two-way sync:
  - When questions are loaded from props → saved to localStorage
  - When component mounts → attempts to restore from localStorage if no props provided

### 2. **Proper State Initialization**
- Added `useEffect` hooks to properly normalize and sync question data
- Ensures `correct_option` field is always set (defaults to 'a' if missing)
- All questions have their state preserved across page refreshes

### 3. **LessonId Prop**
- Updated `QuizQuestionEditor` interface to accept optional `lessonId` prop
- Updated `LessonEditor.tsx` to pass `lessonId` derived from lesson data:
  - Uses `lesson.id` if available: `lesson_{lesson.id}`
  - Falls back to position: `lesson_{module_index}_{lesson_index}`

## Files Modified

### `frontend/src/components/forms/QuizQuestionEditor.tsx`
- Added `useEffect` import
- Added `lessonId` prop to interface and component parameters
- Added two `useEffect` hooks:
  - First hook: Saves questions to localStorage when props change
  - Second hook: Restores persisted questions on component mount
- Added comprehensive logging for debugging

### `frontend/src/components/forms/LessonEditor.tsx`
- Updated `QuizQuestionEditor` component usage to pass `lessonId` prop
- lessonId generation: `lesson.id ? 'lesson_${lesson.id}' : 'lesson_${module_index}_${lesson_index}'`

## How It Works

### When a User Selects "Correct Answer"
1. Radio button `onChange` triggers `updateQuestion(index, 'correct_option', option)`
2. Question state updates in component's `questions` array
3. Parent component `LessonEditor` calls `onUpdate()` to update lesson state
4. First `useEffect` detects the change and saves to localStorage

### When Page Refreshes
1. Component mounts with empty or loading questions
2. LessonEditor provides current questions via props
3. First `useEffect` runs and saves current questions to localStorage
4. If questions haven't fully loaded yet, second `useEffect` restores from localStorage

### When Moving Between Lessons
1. `lessonId` prop changes
2. Both `useEffect` hooks re-run with new `lessonId`
3. Automatically saves/restores data for the new lesson from localStorage

## Debugging
The component logs detailed information for troubleshooting:
```
[QuizQuestionEditor] Initializing with questions: [...]
[QuizQuestionEditor] Restored persisted questions: [...]
```

## Testing the Fix

1. **Edit a quiz lesson** in the course editor
2. **Select a "Correct" checkbox** for any option
3. **Refresh the page** (F5 or Ctrl+R)
4. **Verify the checkbox is still checked** in the same position
5. **Try all four options** to confirm each selection persists

## Browser Support
Works on all modern browsers that support:
- `localStorage` API
- `JSON.stringify()` and `JSON.parse()`
- ES6 destructuring and arrow functions

## Edge Cases Handled

1. **Missing correct_option**: Defaults to 'a'
2. **localStorage disabled/full**: Try-catch prevents errors
3. **Multiple lessons**: Each lesson has isolated localStorage key
4. **New lessons**: Fall back to index-based key if lesson.id not available
5. **Race conditions**: Small delay (100ms) ensures proper timing
