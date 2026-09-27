using System;
using UnityEditor;
using UnityEngine;

namespace UnityBeginnerAssistant.Editor
{
    /// <summary>
    /// Dockable beginner-facing UI. It intentionally teaches one step at a time
    /// instead of overwhelming the learner with an entire tutorial.
    /// </summary>
    public class UnityTutorWindow : EditorWindow
    {
        // These fields are the complete UI state: the learner's question, network
        // progress, retrieved lesson, current teaching step, and optional sections.
        private string question = "";
        private string status = "Start the Python service, then ask a Unity question.";
        private bool waiting;
        private AskResponsePayload answer;
        private int currentStep;
        private Vector2 scroll;
        private bool showVerification;
        private bool showMistakes;

        /// <summary>Create or focus the dockable assistant from Unity's Window menu.</summary>
        [MenuItem("Window/Unity Beginner Assistant")]
        public static void ShowWindow()
        {
            UnityTutorWindow window = GetWindow<UnityTutorWindow>();
            window.titleContent = new GUIContent("Unity Tutor");
            window.minSize = new Vector2(380, 420);
        }

        /// <summary>Render the question form, current status, and lesson every repaint.</summary>
        private void OnGUI()
        {
            scroll = EditorGUILayout.BeginScrollView(scroll);
            EditorGUILayout.Space(8);
            EditorGUILayout.LabelField("Unity Beginner Assistant", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                "Ask what you want to accomplish. The tutor uses the selected GameObject " +
                "and project context to retrieve a verified local lesson.",
                MessageType.Info);

            EditorGUILayout.LabelField("What do you want to do?");
            question = EditorGUILayout.TextArea(question, GUILayout.MinHeight(56));

            EditorGUI.BeginDisabledGroup(waiting || string.IsNullOrWhiteSpace(question));
            if (GUILayout.Button(waiting ? "Finding the best lesson..." : "Guide me"))
                AskQuestion();
            EditorGUI.EndDisabledGroup();

            EditorGUILayout.Space(6);
            EditorGUILayout.LabelField(status, EditorStyles.miniLabel);

            if (answer != null)
                DrawAnswer();

            EditorGUILayout.EndScrollView();
        }

        /// <summary>
        /// Present a lesson progressively: ambiguity first, then one actionable
        /// step, verification, mistakes, and feedback.
        /// </summary>
        private void DrawAnswer()
        {
            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField(answer.title, EditorStyles.largeLabel);
            EditorGUILayout.LabelField(
                $"Match confidence: {answer.confidence:P0}", EditorStyles.miniLabel);
            EditorGUILayout.HelpBox(answer.summary, MessageType.None);

            DrawStringList("Project context", answer.context_notes, MessageType.Warning);

            // Low-confidence retrieval must ask the learner rather than presenting
            // an uncertain lesson as fact.
            if (answer.needs_clarification)
            {
                // Unity help boxes support Info, Warning, Error, and None. Info is
                // the appropriate non-error style for a clarification question.
                EditorGUILayout.HelpBox(answer.clarification, MessageType.Info);
                if (answer.alternatives != null)
                {
                    foreach (AlternativePayload alternative in answer.alternatives)
                    {
                        if (GUILayout.Button(alternative.title))
                        {
                            question = "Teach me how to " + alternative.title;
                            AskQuestion();
                        }
                    }
                }
                return;
            }

            // Only one step is emphasized at a time to reduce cognitive load for a
            // beginner. Previous/next navigation remains under learner control.
            if (answer.steps != null && answer.steps.Length > 0)
            {
                currentStep = Mathf.Clamp(currentStep, 0, answer.steps.Length - 1);
                EditorGUILayout.Space(8);
                EditorGUILayout.LabelField(
                    $"Step {currentStep + 1} of {answer.steps.Length}", EditorStyles.boldLabel);
                EditorGUILayout.HelpBox(answer.steps[currentStep], MessageType.Info);

                EditorGUILayout.BeginHorizontal();
                EditorGUI.BeginDisabledGroup(currentStep == 0);
                if (GUILayout.Button("Previous")) currentStep--;
                EditorGUI.EndDisabledGroup();

                if (currentStep < answer.steps.Length - 1)
                {
                    if (GUILayout.Button("I completed this step")) currentStep++;
                }
                else if (GUILayout.Button("All steps completed"))
                {
                    showVerification = true;
                }
                EditorGUILayout.EndHorizontal();
            }

            showVerification = EditorGUILayout.Foldout(showVerification, "How to verify it worked", true);
            if (showVerification)
                DrawBullets(answer.verification);

            showMistakes = EditorGUILayout.Foldout(showMistakes, "Common mistakes", true);
            if (showMistakes)
                DrawBullets(answer.common_mistakes);

            EditorGUILayout.Space(8);
            EditorGUILayout.LabelField("Was this lesson useful?", EditorStyles.miniLabel);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Yes")) SendFeedback(true);
            if (GUILayout.Button("No")) SendFeedback(false);
            EditorGUILayout.EndHorizontal();
        }

        /// <summary>Render API-generated context warnings as Unity help boxes.</summary>
        private static void DrawStringList(string title, string[] values, MessageType type)
        {
            if (values == null || values.Length == 0) return;
            foreach (string value in values)
                EditorGUILayout.HelpBox($"{title}: {value}", type);
        }

        /// <summary>Render simple readable bullet lists for checks and mistakes.</summary>
        private static void DrawBullets(string[] values)
        {
            if (values == null) return;
            foreach (string value in values)
                EditorGUILayout.LabelField("• " + value, EditorStyles.wordWrappedLabel);
        }

        /// <summary>
        /// Capture context, call Python asynchronously, and reset the lesson UI to
        /// its first step. Errors become visible instructions instead of exceptions.
        /// </summary>
        private async void AskQuestion()
        {
            waiting = true;
            answer = null;
            status = "Collecting Unity context and retrieving a lesson...";
            Repaint();
            try
            {
                answer = await TutorApiClient.Ask(question.Trim(), UnityContextCollector.Capture());
                currentStep = 0;
                showVerification = false;
                showMistakes = false;
                status = $"Matched local lesson: {answer.lesson_id}";
            }
            catch (Exception exception)
            {
                status = exception.Message + "\nRun: .venv\\Scripts\\python.exe main.py";
            }
            finally
            {
                waiting = false;
                Repaint();
            }
        }

        /// <summary>Persist the learner's rating locally for later evaluation.</summary>
        private async void SendFeedback(bool useful)
        {
            try
            {
                await TutorApiClient.SendFeedback(new FeedbackPayload
                {
                    request_id = answer.request_id,
                    lesson_id = answer.lesson_id,
                    question = question,
                    useful = useful
                });
                status = "Thank you. Feedback was saved locally for evaluation.";
            }
            catch (Exception exception)
            {
                status = exception.Message;
            }
            Repaint();
        }
    }
}
