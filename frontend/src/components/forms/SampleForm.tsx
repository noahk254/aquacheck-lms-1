"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { Input, Select, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { contractsApi } from "@/lib/api";

const schema = z.object({
  contract_id: z.coerce.number().min(1, "Select a contract"),
  description: z.string().optional(),
  sample_type: z.string().min(1, "Sample type is required"),
  collection_date: z.string().optional(),
  collection_location: z.string().optional(),
  gps_coordinates: z.string().optional(),
  storage_condition: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface SampleFormProps {
  onSubmit: (data: FormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function SampleForm({ onSubmit, onCancel, loading }: SampleFormProps) {
  const { data: contracts = [] } = useQuery({
    queryKey: ["contracts"],
    queryFn: () => contractsApi.list().then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Select label="Contract" error={errors.contract_id?.message} {...register("contract_id")}>
        <option value="">Select contract...</option>
        {contracts.map((c) => (
          <option key={c.id} value={c.id}>
            {c.contract_number} — {c.title}
          </option>
        ))}
      </Select>

      <Input label="Sample Type" error={errors.sample_type?.message} {...register("sample_type")} placeholder="e.g. Water, Soil, Air" />

      <Textarea
        label="Description"
        error={errors.description?.message}
        {...register("description")}
        rows={2}
        placeholder="Brief description of the sample..."
      />

      <div className="grid grid-cols-2 gap-4">
        <Input label="Collection Date" type="date" error={errors.collection_date?.message} {...register("collection_date")} />
        <Input label="Collection Location" error={errors.collection_location?.message} {...register("collection_location")} placeholder="e.g. Site A, Borehole 3" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input label="GPS Coordinates" error={errors.gps_coordinates?.message} {...register("gps_coordinates")} placeholder="-1.2921, 36.8219" />
        <Input label="Storage Condition" error={errors.storage_condition?.message} {...register("storage_condition")} placeholder="e.g. 4°C, dark" />
      </div>

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
