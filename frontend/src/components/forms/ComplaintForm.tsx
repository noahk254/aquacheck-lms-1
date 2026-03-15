"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { Input, Select, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { customersApi, contractsApi } from "@/lib/api";

const schema = z.object({
  customer_id: z.coerce.number().min(1, "Select a customer"),
  contract_id: z.coerce.number().optional(),
  description: z.string().min(10, "Please provide a detailed description (min 10 characters)"),
  reported_by: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface ComplaintFormProps {
  onSubmit: (data: FormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function ComplaintForm({ onSubmit, onCancel, loading }: ComplaintFormProps) {
  const { data: customers = [] } = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersApi.list().then((r) => r.data),
  });
  const { data: contracts = [] } = useQuery({
    queryKey: ["contracts"],
    queryFn: () => contractsApi.list().then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const handleFormSubmit = (data: FormData) => {
    // Convert empty string / 0 contract_id to undefined
    const cleaned = {
      ...data,
      contract_id: data.contract_id || undefined,
    };
    return onSubmit(cleaned as FormData);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Select label="Customer" error={errors.customer_id?.message} {...register("customer_id")}>
        <option value="">Select customer...</option>
        {customers.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>

      <Select label="Related Contract (optional)" {...register("contract_id")}>
        <option value="">No contract</option>
        {contracts.map((c) => (
          <option key={c.id} value={c.id}>
            {c.contract_number} — {c.title}
          </option>
        ))}
      </Select>

      <Input label="Reported By" error={errors.reported_by?.message} {...register("reported_by")} placeholder="Name of the person reporting" />

      <Textarea
        label="Complaint Description"
        error={errors.description?.message}
        {...register("description")}
        rows={4}
        placeholder="Describe the complaint in detail..."
      />

      <div className="flex gap-3 justify-end pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          Submit Complaint
        </Button>
      </div>
    </form>
  );
}
