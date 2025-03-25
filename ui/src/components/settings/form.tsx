"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { addToast, Button, Spinner, Textarea, Tooltip } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import { getSettings, setSettings } from "@/src/actions/sub";
import { useEffect } from "react";

interface FormValues {
  prompts: { id: number; prompt: string }[];
}

export default function SettingsForm() {
  const { isFetching, data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const { reset, control, register, handleSubmit, formState } =
    useForm<FormValues>({
      defaultValues: { prompts: [] },
    });
  const { isDirty, isValid } = formState;

  useEffect(() => {
    if (!isFetching && settings) {
      // This is done to ensure that the default values are pre-filled by default
      reset(settings);
    }
  }, [isFetching]);

  const {
    fields: promptFields,
    append,
    remove,
  } = useFieldArray({ control, name: "prompts" });

  const onSubmit = async (fv: FormValues) => {
    const updated = await setSettings(fv);
    if (updated) {
      reset(updated);
      addToast({ title: "Settings saved", color: "primary" });
    } else {
      addToast({
        title: "There was an error saving the settings",
        color: "warning",
      });
    }
  };

  return isFetching ? (
    <div className="w-full flex items-center justify-center h-full">
      <Spinner variant="spinner" />
    </div>
  ) : (
    <div className="w-full relative h-full">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full flex gap-4 flex-col relative pb-16"
      >
        <div>
          <h2 className="text-2xl font-bold">Prompts</h2>
          <p className="text-sm text-gray-600">
            Enter the prompts you would like the AI to process. You can add
            multiple prompts by clicking the "Add Prompt" button. Each prompt
            should be descriptive and clear to ensure accurate processing.
          </p>
        </div>

        {promptFields.map((field, index) => (
          <div
            key={field.id}
            className="flex flex-col gap-2 animate-fade-in-out"
          >
            <input
              type="hidden"
              {...register(`prompts.${index}.id` as const)}
              value={field.id}
            />
            <div className="flex gap-2">
              <Textarea
                label={`Prompt ${index + 1} Message`}
                color="primary"
                variant="faded"
                isRequired
                autoCorrect="off"
                {...register(`prompts.${index}.prompt` as const)}
              />

              <Tooltip
                content={
                  promptFields.length === 1
                    ? "You cannot remove the only prompt."
                    : "Remove this prompt"
                }
                delay={0}
                closeDelay={0}
              >
                <div>
                  <Button
                    type="button"
                    onPress={() => remove(index)}
                    className="w-min"
                    color="danger"
                    variant="faded"
                    isDisabled={promptFields.length === 1}
                  >
                    Remove
                  </Button>
                </div>
              </Tooltip>
            </div>

            <div className="flex gap-2 w-full">
              {index === promptFields.length - 1 && (
                <Button
                  type="button"
                  className="w-full"
                  onPress={() => append({ id: -1, prompt: "" })}
                >
                  Add Prompt
                </Button>
              )}
            </div>
          </div>
        ))}

        <div
          className={`w-full transition-opacity duration-300 ${
            isDirty ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          <Button
            isDisabled={!isValid || !isDirty}
            type="submit"
            className="w-full bg-primary text-white"
          >
            Save
          </Button>
        </div>
      </form>
    </div>
  );
}
