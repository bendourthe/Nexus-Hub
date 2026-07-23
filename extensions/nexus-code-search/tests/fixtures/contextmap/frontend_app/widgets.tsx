interface ButtonProps {
  label: string;
  onClick: () => void;
}

export function Button({ label, onClick }: ButtonProps) {
  return <button onClick={onClick}>{label}</button>;
}

type CardProps = { title: string; subtitle?: string };

export const Card: React.FC<CardProps> = ({ title }) => <div>{title}</div>;

// Not a component: a plain helper and a hook, neither PascalCase-exported-component.
function helper() {
  return 1;
}

export const useThing = () => 1;
