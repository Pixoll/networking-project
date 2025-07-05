export function generateHexColors(quantity: number): string[] {
  const colors: string[] = [];

  for (let i = 0; i < quantity; i++) {
    const words = "0123456789ABCDEF";
    let color = "#";

    for (let j = 0; j < 6; j++) {
      color += words[Math.floor(Math.random() * 16)];
    }

    colors.push(color);
  }

  return colors;
}

export async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
