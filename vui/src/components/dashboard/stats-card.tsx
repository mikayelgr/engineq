import { Card } from "@heroui/react";

interface StatsCardProps {
  content: string;
  stats: string;
}

export default function StatsCard({ content, stats }: StatsCardProps) {
  return (
    <Card className="h-full">
      <div className="p-4">
        <h4 className="text-lg font-semibold">{content}</h4>
        <p className="text-2xl">{stats}</p>
      </div>
    </Card>
  );
}
