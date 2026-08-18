const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
  "text/plain",
  "text/csv",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/zip",
  "application/json",
];

const ALLOWED_EXTENSIONS = [
  "pdf", "png", "jpg", "jpeg", "webp", "txt", "csv",
  "doc", "docx", "xls", "xlsx", "zip", "json",
];

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

interface ValidateDocumentRequest {
  file_name: string;
  file_type: string;
  file_size: number;
  category?: string;
}

interface ValidateDocumentSuccess {
  valid: true;
  data: {
    normalized_category: string;
    validation_tag: string;
    checked_at: string;
  };
}

interface ValidateDocumentFailure {
  valid: false;
  errors: string[];
}

function getExtension(fileName: string): string {
  const parts = fileName.toLowerCase().split(".");
  return parts.length > 1 ? parts[parts.length - 1] : "";
}

// A short, deterministic "fingerprint" for this validation event.
// Not a cryptographic hash — just a compact human-readable tag that
// proves the request passed through this function and lets us trace
// which validation pass a given row came from.
function generateValidationTag(fileName: string, fileSize: number): string {
  const base = `${fileName}-${fileSize}-${Date.now()}`;
  let hash = 0;
  for (let i = 0; i < base.length; i++) {
    hash = (hash * 31 + base.charCodeAt(i)) >>> 0;
  }
  return `VLD-${hash.toString(16).toUpperCase()}`;
}

function normalizeCategory(category: string | undefined): string {
  const trimmed = (category ?? "").trim();
  if (trimmed.length === 0) return "General";
  // Title-case it: "finance" -> "Finance", "legal docs" -> "Legal Docs"
  return trimmed
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

Deno.serve(async (req: Request) => {
  // CORS headers so this function can also be called from a browser-based
  // frontend during local testing (the Python backend doesn't need CORS,
  // but including this makes the function reusable and is a common
  // real-world requirement).
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ valid: false, errors: ["Only POST requests are supported."] } as ValidateDocumentFailure),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  let body: ValidateDocumentRequest;
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ valid: false, errors: ["Request body must be valid JSON."] } as ValidateDocumentFailure),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const errors: string[] = [];

  if (!body.file_name || typeof body.file_name !== "string") {
    errors.push("file_name is required and must be a string.");
  }
  if (!body.file_type || typeof body.file_type !== "string") {
    errors.push("file_type is required and must be a string.");
  }
  if (typeof body.file_size !== "number" || body.file_size <= 0) {
    errors.push("file_size is required and must be a positive number.");
  }

  if (errors.length > 0) {
    return new Response(
      JSON.stringify({ valid: false, errors } as ValidateDocumentFailure),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const extension = getExtension(body.file_name);

  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    errors.push(
      `File extension ".${extension}" is not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`,
    );
  }

  if (!ALLOWED_MIME_TYPES.includes(body.file_type)) {
    errors.push(`MIME type "${body.file_type}" is not allowed.`);
  }

  if (body.file_size > MAX_FILE_SIZE_BYTES) {
    errors.push(
      `File is too large (${(body.file_size / (1024 * 1024)).toFixed(2)} MB). Max allowed is ${MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB.`,
    );
  }

  if (errors.length > 0) {
    return new Response(
      JSON.stringify({ valid: false, errors } as ValidateDocumentFailure),
      { status: 422, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }

  const successResponse: ValidateDocumentSuccess = {
    valid: true,
    data: {
      normalized_category: normalizeCategory(body.category),
      validation_tag: generateValidationTag(body.file_name, body.file_size),
      checked_at: new Date().toISOString(),
    },
  };

  return new Response(JSON.stringify(successResponse), {
    status: 200,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});
