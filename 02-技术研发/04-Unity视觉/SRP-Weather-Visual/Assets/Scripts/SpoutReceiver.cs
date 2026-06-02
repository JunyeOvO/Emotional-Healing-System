using UnityEngine;
using Klak.Spout;

public class SpoutReceiver : MonoBehaviour
{
    [SerializeField] private string senderName = "SRP_BreathCircle";

    private Klak.Spout.SpoutReceiver _receiver;
    private Material _displayMaterial;

    void Start()
    {
        _receiver = GetComponent<Klak.Spout.SpoutReceiver>();
        if (!_receiver)
            _receiver = gameObject.AddComponent<Klak.Spout.SpoutReceiver>();

        _receiver.sourceName = senderName;

        var renderer = GetComponent<Renderer>();
        if (renderer)
        {
            _displayMaterial = renderer.material;
            _displayMaterial.SetInt("_ZWrite", 0);
            _displayMaterial.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _displayMaterial.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        }

        Debug.Log($"[SpoutReceiver] Listening for sender: {senderName}");
    }
}
