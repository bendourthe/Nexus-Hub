### Step 7: Implement Accessibility

**ARIA patterns and keyboard navigation**:

```tsx
function Modal({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeRef.current?.focus();                  // Move focus into modal
      const handleKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      };
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal-content">
        <h2 id="modal-title">{title}</h2>
        {children}
        <button ref={closeRef} onClick={onClose} aria-label="Close modal">
          Close
        </button>
      </div>
    </div>
  );
}
```
