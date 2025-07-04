export function generateHexColors(quantity: number): string[] {
    const colors: string[] = [];

    for (let i = 0; i < quantity; i++) {
        const words = '0123456789ABCDEF';
        let color = '#';

        for (let j = 0; j < 6; j++) {
            color += words[Math.floor(Math.random() * 16)];
        }

        colors.push(color);
    }

    return colors;
}

export function getSensorColors(sensorIds: number[]): Record<number, string> {
    const colors = generateHexColors(sensorIds.length);
    const colorMap: Record<number, string> = {};

    sensorIds.forEach((id, index) => {
        colorMap[id] = colors[index];
    });

    return colorMap;
}
