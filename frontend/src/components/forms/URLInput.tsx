"use client";

import { useState, useCallback } from "react";
import Input from "@/components/ui/Input";
import { isValidYouTubeUrl } from "@/lib/utils";
import { Link2 } from "lucide-react";

interface URLInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function URLInput({ value, onChange, disabled }: URLInputProps) {
  const [touched, setTouched] = useState(false);

  const isValid = !value || isValidYouTubeUrl(value);
  const showError = touched && value && !isValid;

  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLInputElement>) => {
      const pasted = e.clipboardData.getData("text");
      if (pasted && isValidYouTubeUrl(pasted)) {
        e.preventDefault();
        onChange(pasted.trim());
        setTouched(true);
      }
    },
    [onChange]
  );

  return (
    <Input
      placeholder="Paste a YouTube URL — e.g. https://youtube.com/watch?v=..."
      value={value}
      onChange={(e) => {
        onChange(e.target.value);
        setTouched(true);
      }}
      onPaste={handlePaste}
      onBlur={() => setTouched(true)}
      disabled={disabled}
      error={showError ? "Please enter a valid YouTube URL" : undefined}
      icon={<Link2 className="w-4 h-4" />}
      autoComplete="off"
    />
  );
}
