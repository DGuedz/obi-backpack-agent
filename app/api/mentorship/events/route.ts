import { NextResponse } from 'next/server';
import { GoogleClient } from '@/app/lib/google';
import path from "node:path";
import { promises as fs } from "node:fs";

export const dynamic = 'force-dynamic';

export async function GET() {
  const googleClient = new GoogleClient();
  
  const missingEnv: string[] = [];
  if (!process.env.GOOGLE_CLIENT_EMAIL) missingEnv.push("GOOGLE_CLIENT_EMAIL");
  if (!process.env.GOOGLE_PRIVATE_KEY) missingEnv.push("GOOGLE_PRIVATE_KEY");

  if (missingEnv.length > 0) {
      await appendAudit({
          event: "mentorship_list",
          status: "error",
          meta: { missingEnv }
      });
      return NextResponse.json({
          connected: false,
          missingEnv,
          events: []
      }, { status: 500 });
  }

  try {
      const events = await googleClient.listUpcomingEvents(5);
      await appendAudit({
          event: "mentorship_list",
          status: "ok"
      });
      return NextResponse.json({
          connected: true,
          events: events
      });
  } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unexpected error';
      await appendAudit({
          event: "mentorship_list",
          status: "error",
          meta: { message }
      });
      return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(req: Request) {
    try {
        const { title, date, email } = await req.json();
        
        const googleClient = new GoogleClient();
        const missingEnv: string[] = [];
        if (!process.env.GOOGLE_CLIENT_EMAIL) missingEnv.push("GOOGLE_CLIENT_EMAIL");
        if (!process.env.GOOGLE_PRIVATE_KEY) missingEnv.push("GOOGLE_PRIVATE_KEY");
        if (missingEnv.length > 0) {
            await appendAudit({
                event: "mentorship_create",
                status: "error",
                meta: { missingEnv }
            });
            return NextResponse.json({ success: false, error: "missing_credentials", missingEnv }, { status: 500 });
        }

        // Criar evento de 1h
        const startTime = new Date(date);
        const endTime = new Date(startTime.getTime() + 3600000); // +1h

        const event = await googleClient.createEvent(
            title || "Mentoria Solo OBIWORK",
            "Sessão individual com Engenheiro OBI.",
            startTime.toISOString(),
            endTime.toISOString(),
            email
        );

        await appendAudit({
            event: "mentorship_create",
            status: "ok",
            meta: { eventId: event?.id ?? null }
        });
        return NextResponse.json({ success: true, event });

    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Unexpected error';
        await appendAudit({
            event: "mentorship_create",
            status: "error",
            meta: { message }
        });
        return NextResponse.json({ error: message }, { status: 500 });
    }
}

async function appendAudit(entry: Record<string, unknown>) {
  const logDir = path.join(process.cwd(), "backend_core", "logs");
  const logPath = path.join(logDir, "audit.jsonl");
  const payload = {
    ts: new Date().toISOString(),
    service: "mentorship",
    ...entry
  };
  try {
    await fs.mkdir(logDir, { recursive: true });
    await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, "utf8");
  } catch {
    return;
  }
}
