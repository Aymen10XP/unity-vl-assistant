using System;

namespace UnityBeginnerAssistant.Editor
{
    // JsonUtility serializes public fields. Snake-case field names deliberately
    // match the Python API, avoiding an additional JSON dependency in Unity.
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

    [Serializable]
    public class AskRequestPayload
    {
        public string question;
        public UnityContextPayload context;
    }

    [Serializable]
    public class AlternativePayload
    {
        public string lesson_id;
        public string title;
        public float score;
    }

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
