using UnityEngine;

public class TravelerWalk : MonoBehaviour
{
    [SerializeField] private float walkDuration = 20f;
    [SerializeField] private float rightBoundary = 10.667f;
    [SerializeField] private float leftBoundary = -10.667f;

    private Animator animator;
    private SpriteRenderer spriteRenderer;
    private float startX;
    private float targetX;
    private float elapsed;
    private bool walking;

    void Start()
    {
        animator = GetComponent<Animator>();
        spriteRenderer = GetComponent<SpriteRenderer>();

        startX = transform.position.x;
        targetX = leftBoundary;

        animator.Play("Walk");
        walking = true;
    }

void Update()
    {
        if (!walking) return;

        elapsed += Time.deltaTime;
        float t = elapsed / walkDuration;
        if (t >= 1f)
        {
            t = 1f;
            walking = false;
            animator.Play("Idle");
        }

        float newX = Mathf.Lerp(startX, targetX, t);
        transform.position = new Vector3(newX, transform.position.y, transform.position.z);
    }
}
