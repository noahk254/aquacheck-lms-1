import React from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn("bg-white rounded-xl shadow-sm border border-gray-200", className)}>
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, action, className }: CardHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between px-6 py-4 border-b border-gray-100", className)}>
      <div>
        <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function CardBody({ children, className }: CardBodyProps) {
  return <div className={cn("px-6 py-4", className)}>{children}</div>;
}

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: "blue" | "green" | "yellow" | "red" | "purple" | "gray";
}

const colorMap = {
  blue: "bg-primary-50 text-primary-600",
  green: "bg-green-50 text-green-600",
  yellow: "bg-yellow-50 text-yellow-600",
  red: "bg-red-50 text-red-600",
  purple: "bg-purple-50 text-purple-600",
  gray: "bg-gray-50 text-gray-600",
};

export function StatCard({ title, value, subtitle, icon, color = "blue" }: StatCardProps) {
  return (
    <Card>
      <div className="p-5 flex items-center gap-4">
        {icon && (
          <div className={cn("p-3 rounded-xl flex-shrink-0", colorMap[color])}>
            {icon}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </Card>
  );
}
