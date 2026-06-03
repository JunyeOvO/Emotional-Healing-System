using UnityEngine;

public class WalkBG05 : MonoBehaviour
{
    [Header("Bridge Zone (bg05)")]
    public float xStart = 74.667f;
    public float xEnd = 96f;
    public float bridgeWorldY = -3.749f;

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
            animator.Play("Idle");
        }

        UpdatePosition();
        if (spriteRenderer) spriteRenderer.flipX = true;
    }

    void UpdatePosition()
    {
        transform.position = new Vector3(currentX, bridgeWorldY, 0);
    }
}
