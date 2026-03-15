"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { Input, Select, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { customersApi } from "@/lib/api";

const schema = z.object({
  customer_id: z.coerce.number().min(1, "Select a customer"),
  title: z.string().min(2, "Title is required"),
  scope_of_work: z.string().optional(),
  decision_rules: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface ContractFormProps {
  onSubmit: (data: FormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function ContractForm({ onSubmit, onCancel, loading }: ContractFormProps) {
  const { data: customers = [] } = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersApi.list().then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Select label="Customer" error={errors.customer_id?.message} {...register("customer_id")}>
        <option value="">Select customer...</option>
        {customers.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>

      <Input label="Contract Title" error={errors.title?.message} {...register("title")} placeholder="e.g. Water Quality Testing Q1 2024" />

      <Textarea
        label="Scope of Work"
        error={errors.scope_of_work?.message}
        {...register("scope_of_work")}
        rows={3}
        placeholder="Describe the scope of testing work..."
      />

      <Textarea
        label="Decision Rules"
        error={errors.decision_rules?.message}
        {...register("decision_rules")}
        rows={2}
        placeholder="Specify decision rules (e.g. pass/fail criteria)..."
      />

      <div className="flex gap-3 justify-end pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          Create Contract
        </Button>
      </div>
    </form>
  );
}
