"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatCard } from "@/components/ui/Card";
import { qualityApi } from "@/lib/api";
import { AlertTriangle, MessageSquareWarning, Wrench, Activity } from "lucide-react";

export default function QualityPage() {
  const [search, setSearch] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");

  const { data: dash } = useQuery({
    queryKey: ["quality-dashboard"],
    queryFn: () => qualityApi.dashboard().then((r) => r.data),
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ["audit-logs", resourceFilter],
    queryFn: () => qualityApi.auditLogs({ limit: 100, resource_type: resourceFilter || undefined }).then((r) => r.data),
  });

  const filteredLogs = (logsData?.items ?? []).filter((l) =>
    !search ||
    l.action.toLowerCase().includes(search.toLowerCase()) ||
    l.resource_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <DashboardLayout title="Quality Management">
      <div className="space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Open NCs (High)" value={dash?.open_ncs_by_risk.high ?? 0} icon={<AlertTriangle className="w-5 h-5" />} color="red" />
          <StatCard title="Open NCs (Medium)" value={dash?.open_ncs_by_risk.medium ?? 0} icon={<AlertTriangle className="w-5 h-5" />} color="yellow" />
          <StatCard title="Open Complaints" value={dash?.open_complaints ?? 0} icon={<MessageSquareWarning className="w-5 h-5" />} color="red" />
          <StatCard title="Calibration Due" value={dash?.equipment_calibration_due ?? 0} icon={<Wrench className="w-5 h-5" />} color="yellow" />
        </div>

        {/* QA Alerts */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-primary-500" />
            <h3 className="font-semibold text-gray-900 text-sm">QA Alerts</h3>
          </div>
          <div className="space-y-2">
            {(dash?.open_ncs_by_risk.high ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
                <span className="text-sm text-red-800">
                  {dash?.open_ncs_by_risk.high} high-risk non-conformit{dash?.open_ncs_by_risk.high === 1 ? "y" : "ies"} require immediate attention.
                </span>
              </div>
            )}
            {(dash?.equipment_calibration_due ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <Wrench className="w-4 h-4 text-yellow-600 flex-shrink-0" />
                <span className="text-sm text-yellow-800">
                  {dash?.equipment_calibration_due} equipment item{dash?.equipment_calibration_due === 1 ? "" : "s"} due for calibration within 30 days.
                </span>
              </div>
            )}
            {(dash?.open_complaints ?? 0) > 0 && (
              <div className="flex items-center gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <MessageSquareWarning className="w-4 h-4 text-orange-600 flex-shrink-0" />
                <span className="text-sm text-orange-800">
                  {dash?.open_complaints} open complaint{dash?.open_complaints === 1 ? "" : "s"} pending resolution.
                </span>
              </div>
            )}
            {(dash?.open_ncs_by_risk.high ?? 0) === 0 &&
              (dash?.equipment_calibration_due ?? 0) === 0 &&
              (dash?.open_complaints ?? 0) === 0 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
                  No active QA alerts. System is operating normally.
                </div>
              )}
          </div>
        </div>

        {/* Audit Logs */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="px-5 py-4 border-b border-gray-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <h3 className="font-semibold text-gray-900 text-sm">Audit Log</h3>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Search logs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:border-primary-400 outline-none w-44"
              />
              <select
                value={resourceFilter}
                onChange={(e) => setResourceFilter(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:border-primary-400 outline-none bg-white"
              >
                <option value="">All Resources</option>
                {["user", "contract", "sample", "test_result", "equipment", "report", "complaint", "nonconformity"].map((r) => (
                  <option key={r} value={r}>{r.replace("_", " ")}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  {["#", "Action", "Resource", "Resource ID", "User ID", "IP", "Time"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logsLoading ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
                ) : filteredLogs.length === 0 ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No audit log entries.</td></tr>
                ) : filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 text-gray-400 text-xs">{log.id}</td>
                    <td className="px-4 py-2.5 font-medium text-gray-800 text-xs">{log.action}</td>
                    <td className="px-4 py-2.5 text-gray-600 text-xs capitalize">{log.resource_type}</td>
                    <td className="px-4 py-2.5 text-gray-500 font-mono text-xs">{log.resource_id ?? "—"}</td>
                    <td className="px-4 py-2.5 text-gray-500 text-xs">{log.user_id ?? "system"}</td>
                    <td className="px-4 py-2.5 text-gray-400 text-xs">{log.ip_address ?? "—"}</td>
                    <td className="px-4 py-2.5 text-gray-400 text-xs">{log.created_at ? format(new Date(log.created_at), "MMM d, HH:mm") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
