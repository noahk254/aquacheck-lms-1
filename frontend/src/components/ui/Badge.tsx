import React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "gray"
  | "blue"
  | "yellow"
  | "red"
  | "green"
  | "purple";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-gray-100 text-gray-700",
  success: "bg-green-100 text-green-800",
  warning: "bg-yellow-100 text-yellow-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-primary-100 text-primary-700",
  gray: "bg-gray-100 text-gray-700",
  blue: "bg-blue-100 text-blue-800",
  yellow: "bg-yellow-100 text-yellow-800",
  red: "bg-red-100 text-red-800",
  green: "bg-green-100 text-green-800",
  purple: "bg-purple-100 text-purple-800",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

// Convenience helpers for domain statuses
export function ContractStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    draft: "gray",
    under_review: "yellow",
    approved: "success",
    rejected: "danger",
    completed: "blue",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}

export function SampleStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    received: "info",
    registered: "blue",
    assigned: "yellow",
    in_testing: "warning",
    completed: "success",
    archived: "gray",
    disposed: "gray",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}

export function TestStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    pending: "gray",
    in_progress: "yellow",
    completed: "blue",
    validated: "success",
    failed: "danger",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}

export function EquipmentStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    active: "success",
    in_calibration: "yellow",
    out_of_service: "danger",
    decommissioned: "gray",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}

export function RiskLevelBadge({ level }: { level: string }) {
  const map: Record<string, BadgeVariant> = {
    low: "success",
    medium: "yellow",
    high: "danger",
  };
  return <Badge variant={map[level] ?? "default"}>{level}</Badge>;
}

export function MethodStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    draft: "gray",
    validated: "success",
    deprecated: "danger",
  };
  return <Badge variant={map[status] ?? "default"}>{status}</Badge>;
}

export function ReportStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    draft: "gray",
    under_review: "yellow",
    issued: "success",
    amended: "warning",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}

export function ComplaintStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    received: "info",
    under_investigation: "yellow",
    corrective_action: "warning",
    closed: "success",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace("_", " ")}</Badge>;
}
