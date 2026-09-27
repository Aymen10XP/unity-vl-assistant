using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace UnityBeginnerAssistant.Editor
{
    /// <summary>Minimal localhost HTTP client; it contains no model logic.</summary>
    public static class TutorApiClient
    {
        private const string BaseUrl = "http://127.0.0.1:8765";

        /// <summary>
        /// Serialize a learner question and Unity context, then deserialize the
        /// grounded lesson returned by Python.
        /// </summary>
        public static async Task<AskResponsePayload> Ask(
            string question,
            UnityContextPayload context)
        {
            AskRequestPayload payload = new AskRequestPayload
            {
                question = question,
                context = context
            };
            string json = JsonUtility.ToJson(payload);
            string response = await PostJson("/ask", json);
            return JsonUtility.FromJson<AskResponsePayload>(response);
        }

        /// <summary>Send a thumbs-up/down rating without blocking the Editor.</summary>
        public static async Task SendFeedback(FeedbackPayload payload)
        {
            await PostJson("/feedback", JsonUtility.ToJson(payload));
        }

        /// <summary>
        /// Shared JSON POST implementation. Keeping network mechanics here leaves
        /// the Editor window focused only on presentation and learner interaction.
        /// </summary>
        private static async Task<string> PostJson(string route, string json)
        {
            // UnityWebRequest needs raw UTF-8 bytes for a JSON request body.
            byte[] body = Encoding.UTF8.GetBytes(json);
            using (UnityWebRequest request = new UnityWebRequest(BaseUrl + route, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(body);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                UnityWebRequestAsyncOperation operation = request.SendWebRequest();

                // Yielding keeps the Unity Editor responsive while Python works.
                while (!operation.isDone)
                    await Task.Yield();

                // Preserve the Python error body because it is far more useful for
                // debugging than Unity's short transport error by itself.
                if (request.result != UnityWebRequest.Result.Success)
                    throw new Exception($"Tutor API error: {request.error}\n{request.downloadHandler.text}");

                return request.downloadHandler.text;
            }
        }
    }
}
