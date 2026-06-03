using UnityEngine;

public class WalkBG04 : MonoBehaviour
{
    [Header("Bridge Zone (bg04)")]
    public float xStart = 53.333f;
    public float xEnd = 74.667f;
    public float bridgeWorldY = -3.787f;

    [Header("Chain")]
    public MonoBehaviour nextWalker;

    [Header("Walking")]
    public float walkSpeed = 2.2f;

    private Animator animator;
    private SpriteRenderer spriteRenderer;
    private float currentX;
    private bool walking;

    void OnEnable()
    {
        animator = GetComponent<Animator>();
        spriteRenderer = GetComponent<SpriteRenderer>();

        currentX = xStart;
        UpdatePosition();
        animator.Play("Walk");
        walking = true;
    }

    void Update()
    {
        if (!walking) return;

        currentX += walkSpeed * Time.deltaTime;
        if (currentX >= xEnd)
        {
            currentX = xEnd;
            walking = false;
            enabled = false;
            if (nextWalker != null) nextWalker.enabled = true;
        }

        UpdatePosition();
        if (spriteRenderer) spriteRenderer.flipX = true;
    }

    void UpdatePosition()
    {
        transform.position = new Vector3(currentX, bridgeWorldY, 0);
    }
}
