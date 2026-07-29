import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useDismissOnOutsideOrEscape } from "./useDismissOnOutsideOrEscape";

function MenuFixture({ onDismiss }: { onDismiss: () => void }) {
  const ref = useDismissOnOutsideOrEscape<HTMLDivElement>(true, onDismiss);
  return (
    <div>
      <div ref={ref} data-testid="menu">
        <button type="button">Item du menu</button>
      </div>
      <button type="button">Bouton hors du menu</button>
    </div>
  );
}

describe("useDismissOnOutsideOrEscape", () => {
  it("appelle onDismiss au clic en dehors du conteneur référencé", async () => {
    const onDismiss = vi.fn();
    const user = userEvent.setup();
    render(<MenuFixture onDismiss={onDismiss} />);

    await user.click(screen.getByText("Bouton hors du menu"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("n'appelle pas onDismiss au clic à l'intérieur du conteneur", async () => {
    const onDismiss = vi.fn();
    const user = userEvent.setup();
    render(<MenuFixture onDismiss={onDismiss} />);

    await user.click(screen.getByText("Item du menu"));
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it("appelle onDismiss sur Échap", async () => {
    const onDismiss = vi.fn();
    const user = userEvent.setup();
    render(<MenuFixture onDismiss={onDismiss} />);

    await user.keyboard("{Escape}");
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("ne s'attache pas quand isOpen est false", async () => {
    function ClosedMenuFixture({ onDismiss }: { onDismiss: () => void }) {
      const ref = useDismissOnOutsideOrEscape<HTMLDivElement>(false, onDismiss);
      return <div ref={ref} data-testid="menu" />;
    }
    const onDismiss = vi.fn();
    const user = userEvent.setup();
    render(<ClosedMenuFixture onDismiss={onDismiss} />);

    await user.keyboard("{Escape}");
    expect(onDismiss).not.toHaveBeenCalled();
  });
});
