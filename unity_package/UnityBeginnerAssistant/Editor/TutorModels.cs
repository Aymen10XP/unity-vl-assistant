using System;

namespace UnityBeginnerAssistant.Editor
{
    // JsonUtility serializes public fields. Snake-case field names deliberately
    // match the Python API, avoiding an additional JSON dependency in Unity.
    /// <summary>Safe Editor facts that improve lesson selection.</summary>
    [Serializable]
    public class UnityContextPayload
    {
        public string unity_version = "unknown";
        public string project_dimension = "unknown";
        public string render_pipeline = "unknown";
        public string active_scene = "";
        public string selected_object = "";
        public string[] selected_components = Array.Empty<string>();
        public string[] installed_packages = Array.Empty<string>();
        public bool is_playing;
    }

    /// <summary>Body sent to POST /ask.</summary>
    [Serializable]
    public class AskRequestPayload
    {
        public string question;
        public UnityContextPayload context;
    }

    /// <summary>A candidate lesson offered when the question is ambiguous.</summary>
    [Serializable]
    public class AlternativePayload
    {
        public string lesson_id;
        public string title;
        public float score;
    }

    /// <summary>Grounded lesson and UI state returned by the Python service.</summary>
    [Serializable]
    public class AskResponsePayload
    {
        public string request_id;
        public string lesson_id;
        public string title;
        public string summary;
        public string[] steps;
        public string[] verification;
        public string[] common_mistakes;
        public string[] context_notes;
        public float confidence;
        public bool needs_clarification;
        public string clarification;
        public AlternativePayload[] alternatives;
    }

    /// <summary>Small local rating used to measure and improve usefulness.</summary>
    [Serializable]
    public class FeedbackPayload
    {
        public string request_id;
        public string lesson_id;
        public string question;
        public bool useful;
        public string comment = "";
    }
}
