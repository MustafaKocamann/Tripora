interface InstructionsPanelProps {
  instructions: string;
}

export function InstructionsPanel({
  instructions,
}: Readonly<InstructionsPanelProps>) {
  return (
    <main className="instructions-panel">
      <p className="eyebrow">Read only</p>
      <h2>Agent instructions</h2>
      <pre>{instructions}</pre>
    </main>
  );
}
