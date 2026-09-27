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

        public static async Task SendFeedback(FeedbackPayload payload)
        {
            await PostJson("/feedback", JsonUtility.ToJson(payload));
        }

        private static async Task<string> PostJson(string route, string json)
        {
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

                if (request.result != UnityWebRequest.Result.Success)
                    throw new Exception($"Tutor API error: {request.error}\n{request.downloadHandler.text}");

                return request.downloadHandler.text;
            }
        }
    }
}
