"use client";

import { Bell } from "lucide-react";
import { getCurrentUser } from "@/lib/auth";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const user = getCurrentUser();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
      <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary-400 rounded-full" />
        </button>
        <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
          <div className="w-8 h-8 rounded-full bg-primary-400 flex items-center justify-center text-white text-xs font-bold">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? "?"}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-gray-900 leading-tight">{user?.full_name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role?.replace("_", " ")}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
