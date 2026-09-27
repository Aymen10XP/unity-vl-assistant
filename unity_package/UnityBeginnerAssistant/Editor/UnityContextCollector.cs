using System.Linq;
using UnityEditor;
using UnityEditor.PackageManager;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace UnityBeginnerAssistant.Editor
{
    /// <summary>
    /// Collects only small, structured facts. No screenshot, source file, or
    /// scene asset is uploaded; the API runs locally on 127.0.0.1.
    /// </summary>
    public static class UnityContextCollector
    {
        public static UnityContextPayload Capture()
        {
            GameObject selected = Selection.activeGameObject;
            string[] components = selected == null
                ? new string[0]
                : selected.GetComponents<Component>()
                    .Where(component => component != null)
                    .Select(component => component.GetType().Name)
                    .Distinct()
                    .ToArray();

            string[] packages;
            try
            {
                // Package lookup happens only when the learner asks a question.
                packages = PackageInfo.GetAllRegisteredPackages()
                    .Select(package => package.name)
                    .ToArray();
            }
            catch
            {
                // Tutor guidance still works if Package Manager is refreshing.
                packages = new string[0];
            }

            return new UnityContextPayload
            {
                unity_version = Application.unityVersion,
                project_dimension = EditorSettings.defaultBehaviorMode == EditorBehaviorMode.Mode2D
                    ? "2D"
                    : "3D",
                render_pipeline = GraphicsSettings.currentRenderPipeline == null
                    ? "Built-in"
                    : GraphicsSettings.currentRenderPipeline.GetType().Name,
                active_scene = SceneManager.GetActiveScene().name,
                selected_object = selected == null ? "" : selected.name,
                selected_components = components,
                installed_packages = packages,
                is_playing = EditorApplication.isPlaying
            };
        }
    }
}
