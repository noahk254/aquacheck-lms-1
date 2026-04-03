"use client";

import { useForm, useController, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { Input, Select, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { contractsApi, customersApi, testCatalogApi } from "@/lib/api";
import type { TestCatalogItem } from "@/lib/types";
import { FlaskConical, Microscope } from "lucide-react";

const schema = z.object({
  customer_id: z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : value),
    z.coerce.number().int().positive().optional()
  ),
  contract_id: z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : value),
    z.coerce.number().int().positive().optional()
  ),
  description: z.string().optional(),
  sample_type: z.string().min(1, "Sample type is required"),
  collection_date: z.string().optional(),
  collection_location: z.string().optional(),
  gps_coordinates: z.string().optional(),
  storage_condition: z.string().optional(),
  requested_test_ids: z.array(z.number().int().positive()).default([]),
});

type FormData = z.infer<typeof schema>;

interface SampleFormProps {
  onSubmit: (data: FormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  customerId?: number;
}

// ─── Test picker component ────────────────────────────────────────────────────

function TestPicker({ control, catalogItems }: { control: Control<FormData>; catalogItems: TestCatalogItem[] }) {
  const { field } = useController({ control, name: "requested_test_ids" });
  const selected: number[] = field.value ?? [];

  function toggle(id: number) {
    const next = selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id];
    field.onChange(next);
  }

  function toggleGroup(ids: number[]) {
    const allSelected = ids.every((id) => selected.includes(id));
    if (allSelected) {
      field.onChange(selected.filter((id) => !ids.includes(id)));
    } else {
      const toAdd = ids.filter((id) => !selected.includes(id));
      field.onChange([...selected, ...toAdd]);
    }
  }

  const physio = catalogItems.filter((i) => i.category === "physicochemical");
  const micro = catalogItems.filter((i) => i.category === "microbiological");

  const physioIds = physio.map((i) => i.id);
  const microIds = micro.map((i) => i.id);

  const allPhysioSelected = physioIds.length > 0 && physioIds.every((id) => selected.includes(id));
  const allMicroSelected = microIds.length > 0 && microIds.every((id) => selected.includes(id));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Tests to be Performed
        </label>
        {selected.length > 0 && (
          <span className="text-xs text-primary-600 font-medium bg-primary-50 px-2 py-0.5 rounded-full">
            {selected.length} selected
          </span>
        )}
      </div>

      {/* Physicochemical */}
      {physio.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border-b border-gray-200">
            <FlaskConical className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-xs font-semibold text-blue-800 uppercase tracking-wide">Physio-Chemical</span>
            <label className="ml-auto flex items-center gap-1.5 text-xs text-blue-700 cursor-pointer">
              <input
                type="checkbox"
                checked={allPhysioSelected}
                onChange={() => toggleGroup(physioIds)}
                className="rounded border-blue-300"
              />
              Select all
            </label>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 max-h-52 overflow-y-auto">
            {physio.map((item) => (
              <label key={item.id} className="flex items-start gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-50">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => toggle(item.id)}
                  className="mt-0.5 rounded border-gray-300 flex-shrink-0"
                />
                <span className="text-sm text-gray-700 leading-tight">{item.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Microbiological */}
      {micro.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border-b border-gray-200">
            <Microscope className="w-3.5 h-3.5 text-green-600" />
            <span className="text-xs font-semibold text-green-800 uppercase tracking-wide">Microbiological</span>
            <label className="ml-auto flex items-center gap-1.5 text-xs text-green-700 cursor-pointer">
              <input
                type="checkbox"
                checked={allMicroSelected}
                onChange={() => toggleGroup(microIds)}
                className="rounded border-green-300"
              />
              Select all
            </label>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 max-h-36 overflow-y-auto">
            {micro.map((item) => (
              <label key={item.id} className="flex items-start gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-50">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => toggle(item.id)}
                  className="mt-0.5 rounded border-gray-300 flex-shrink-0"
                />
                <span className="text-sm text-gray-700 leading-tight">{item.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {catalogItems.length === 0 && (
        <p className="text-sm text-gray-400 italic">No catalog tests available.</p>
      )}
    </div>
  );
}

// ─── Main form ────────────────────────────────────────────────────────────────

export function SampleForm({ onSubmit, onCancel, loading, customerId }: SampleFormProps) {
  const isCustomer = customerId !== undefined;

  const { data: customers = [] } = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersApi.list().then((r) => r.data),
    enabled: !isCustomer,
  });

  const { data: contracts = [] } = useQuery({
    queryKey: ["contracts"],
    queryFn: () => contractsApi.list().then((r) => r.data),
  });

  const { data: catalogItems = [] } = useQuery({
    queryKey: ["test-catalog"],
    queryFn: () => testCatalogApi.list({ active_only: true }).then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { customer_id: customerId, requested_test_ids: [] },
  });

  const selectedCustomerId = watch("customer_id");
  const effectiveCustomerId = isCustomer ? customerId : selectedCustomerId;

  const filteredContracts = effectiveCustomerId
    ? contracts.filter((c) => c.customer_id === effectiveCustomerId)
    : contracts;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Customer selector — hidden for customer-role users */}
      {!isCustomer && (
        <Select label="Customer (optional)" error={errors.customer_id?.message} {...register("customer_id")}>
          <option value="">No specific customer</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
      )}

      <div className="space-y-2">
        <Select label="Contract (optional)" error={errors.contract_id?.message} {...register("contract_id")}>
          <option value="">Standalone sample (no contract)</option>
          {filteredContracts.map((c) => (
            <option key={c.id} value={c.id}>
              {c.contract_number} — {c.title}
            </option>
          ))}
        </Select>

        <p className="text-xs text-gray-500">
          Leave this blank to register a standalone sample. Only samples linked to a contract can proceed to testing.
        </p>
      </div>

      <Input label="Sample Type" error={errors.sample_type?.message} {...register("sample_type")} placeholder="e.g. Dialysis Water, Potable Water" />

      <Textarea
        label="Description"
        error={errors.description?.message}
        {...register("description")}
        rows={2}
        placeholder="Brief description of the sample..."
      />

      <div className="grid grid-cols-2 gap-4">
        <Input label="Collection Date" type="date" error={errors.collection_date?.message} {...register("collection_date")} />
        <Input label="Collection Location" error={errors.collection_location?.message} {...register("collection_location")} placeholder="e.g. Dialysis Unit, Ward 3" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input label="GPS Coordinates" error={errors.gps_coordinates?.message} {...register("gps_coordinates")} placeholder="-1.2921, 36.8219" />
        <Input label="Storage Condition" error={errors.storage_condition?.message} {...register("storage_condition")} placeholder="e.g. 4°C, dark" />
      </div>

      {/* Test selection */}
      <TestPicker control={control} catalogItems={catalogItems} />

      <div className="flex gap-3 justify-end pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          Register Sample
        </Button>
      </div>
    </form>
  );
}
