"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Textarea } from "@heroui/react";

const promptSchema = z.object({
  id: z.string(),
  prompt: z.string().nonempty("Prompt is required"),
});

const schema = z.object({
  prompts: z.array(promptSchema).min(1, "You must have at least one prompt."),
});

type FormValues = z.infer<typeof schema>;

export default function SettingsForm() {
  const {
    register,
    control,
    handleSubmit,
    formState: { isDirty },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const {
    fields: promptFields,
    append,
    remove,
  } = useFieldArray({ control, name: "prompts" });

  const onSubmit = (data: FormValues) => {
    console.log(data);
    // Add your save logic here
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="w-full flex gap-4 flex-col relative pb-16"
    >
      <h2 className="text-2xl font-bold">Prompts</h2>
      {promptFields.map((field, index) => (
        <div key={field.id} className="flex flex-col gap-2 animate-fade-in-out">
          <Textarea
            label={`Prompt ${index + 1}`}
            color="primary"
            variant="faded"
            isRequired
            {...register(`prompts.${index}.prompt` as const)}
            autoCorrect="off"
          />

          <Button
            type="button"
            onPress={() => remove(index)}
            className="self-end"
            isDisabled={promptFields.length === 1}
          >
            Remove
          </Button>
        </div>
      ))}

      <Button
        type="button"
        onPress={() => append({ id: `${promptFields.length + 1}`, prompt: "" })}
      >
        Add Prompt
      </Button>

      {isDirty && (
        <Button type="submit" className="w-full mt-4">
          Save
        </Button>
      )}
    </form>
  );
}
