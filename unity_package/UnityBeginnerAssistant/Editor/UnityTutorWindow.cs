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
        private bool serviceConnectionError;
        private string technicalError = "";

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

            EditorGUILayout.BeginHorizontal();
            EditorGUI.BeginDisabledGroup(waiting || string.IsNullOrWhiteSpace(question));
            if (GUILayout.Button(waiting ? "Finding the best lesson..." : "Guide me"))
                AskQuestion();
            EditorGUI.EndDisabledGroup();

            EditorGUI.BeginDisabledGroup(waiting || (answer == null && string.IsNullOrEmpty(question)));
            if (GUILayout.Button("Clear / New question", GUILayout.Width(145)))
            {
                ClearQuestion();
                GUI.FocusControl(null);
            }
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(6);
            EditorGUILayout.HelpBox(status,
                waiting ? MessageType.Info :
                answer != null ? MessageType.None : MessageType.Info);

            if (serviceConnectionError)
            {
                EditorGUILayout.HelpBox(
                    "The tutor service is not reachable at http://127.0.0.1:8765.\n\n" +
                    "1. Open a terminal in the cloned unity-vl-assistant folder.\n" +
                    "2. Run the command below.\n" +
                    "3. Keep that terminal open and click Retry.",
                    MessageType.Error);

                EditorGUILayout.TextField(
                    ".venv\\Scripts\\python.exe main.py",
                    EditorStyles.textField);

                EditorGUILayout.BeginHorizontal();
                if (GUILayout.Button("Copy start command"))
                    GUIUtility.systemCopyBuffer = ".venv\\Scripts\\python.exe main.py";
                if (GUILayout.Button("Retry"))
                    AskQuestion();
                EditorGUILayout.EndHorizontal();

                showVerification = EditorGUILayout.Foldout(
                    showVerification, "Technical connection details", false);
                if (showVerification)
                    EditorGUILayout.HelpBox(technicalError, MessageType.None);
            }

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
            EditorGUILayout.LabelField("Recommended lesson", EditorStyles.boldLabel);
            EditorGUILayout.LabelField(answer.title, EditorStyles.largeLabel);
            EditorGUILayout.LabelField(GetConfidenceLabel(answer.confidence), EditorStyles.miniLabel);
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
                        if (GUILayout.Button(
                            $"{alternative.title}  ({alternative.score:P0} match)",
                            GUILayout.MinHeight(28)))
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
                    $"Current step  •  {currentStep + 1} of {answer.steps.Length}", EditorStyles.boldLabel);
                EditorGUILayout.LabelField("DO THIS", EditorStyles.miniBoldLabel);
                EditorGUILayout.HelpBox(answer.steps[currentStep], MessageType.Info);

                EditorGUILayout.BeginHorizontal();
                EditorGUI.BeginDisabledGroup(currentStep == 0);
                if (GUILayout.Button("Previous")) currentStep--;
                EditorGUI.EndDisabledGroup();

                if (currentStep < answer.steps.Length - 1)
                {
                    if (GUILayout.Button("I completed this step  →", GUILayout.MinHeight(28))) currentStep++;
                }
                else if (GUILayout.Button("All steps completed"))
                {
                    showVerification = true;
                }
                EditorGUILayout.EndHorizontal();

                EditorGUILayout.Space(4);
                DrawStepProgress(answer.steps.Length);
            }

            showVerification = EditorGUILayout.Foldout(
                showVerification, "How to verify it worked", true);
            if (showVerification)
                DrawBullets(answer.verification);

            showMistakes = EditorGUILayout.Foldout(showMistakes, "Common mistakes", true);
            if (showMistakes)
                DrawBullets(answer.common_mistakes);

            EditorGUILayout.Space(8);
            EditorGUILayout.LabelField("Was this lesson useful?", EditorStyles.miniLabel);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Yes, this helped")) SendFeedback(true);
            if (GUILayout.Button("No, try another result")) SendFeedback(false);
            EditorGUILayout.EndHorizontal();
        }

        /// <summary>Turn the retrieval score into a plain-language confidence label.</summary>
        private static string GetConfidenceLabel(float confidence)
        {
            if (confidence >= 0.70f)
                return $"Strong match  •  {confidence:P0}";
            if (confidence >= 0.50f)
                return $"Possible match  •  {confidence:P0}";
            return $"Low confidence  •  {confidence:P0}";
        }

        /// <summary>Show how far the learner has moved through the lesson.</summary>
        private void DrawStepProgress(int stepCount)
        {
            if (stepCount <= 1) return;

            EditorGUILayout.BeginHorizontal();
            for (int index = 0; index < stepCount; index++)
            {
                GUIStyle style = index == currentStep
                    ? EditorStyles.boldLabel
                    : EditorStyles.miniLabel;
                GUILayout.Label(index <= currentStep ? "●" : "○", style,
                    GUILayout.Width(18));
            }
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
            serviceConnectionError = false;
            technicalError = "";
            answer = null;
            status = "Collecting Unity context and retrieving a lesson...";
            Repaint();
            try
            {
                answer = await TutorApiClient.Ask(question.Trim(), UnityContextCollector.Capture());
                currentStep = 0;
                showVerification = false;
                showMistakes = false;
                status = answer.needs_clarification
                    ? "A few lessons could fit. Choose the closest goal below."
                    : $"Lesson ready: {answer.title}";
            }
            catch (Exception exception)
            {
                technicalError = exception.Message;
                serviceConnectionError = IsConnectionError(exception.Message);
                status = serviceConnectionError
                    ? "Tutor service is not running."
                    : $"The tutor could not complete the request.";
            }
            finally
            {
                waiting = false;
                Repaint();
            }
        }

        /// <summary>Distinguish a stopped local service from API or lesson errors.</summary>
        private static bool IsConnectionError(string error)
        {
            if (string.IsNullOrEmpty(error)) return false;
            string text = error.ToLowerInvariant();
            return text.Contains("cannot connect") ||
                   text.Contains("connection refused") ||
                   text.Contains("could not resolve") ||
                   text.Contains("destination host") ||
                   text.Contains("network is unreachable") ||
                   text.Contains("timed out");
        }

        /// <summary>Reset all lesson state so the learner can start a fresh question.</summary>
        private void ClearQuestion()
        {
            question = "";
            answer = null;
            currentStep = 0;
            showVerification = false;
            showMistakes = false;
            serviceConnectionError = false;
            technicalError = "";
            scroll = Vector2.zero;
            status = "Ready for a new Unity question.";
            Repaint();
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
