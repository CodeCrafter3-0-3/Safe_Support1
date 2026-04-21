import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { resText } = await req.json();

    if (!resText) {
      return NextResponse.json({ error: 'Text is required' }, { status: 400 });
    }

    if (!process.env.GROQ_API_KEY) {
      console.error("CRITICAL ERROR: GROQ_API_KEY is missing from environment variables!");
      return NextResponse.json({ error: 'Missing API Key' }, { status: 500 });
    }

    const prompt = `You are an intelligent data extraction AI. Extract the following incident report into a JSON object.
If a specific detail (like the relationship with the perpetrator, the frequency, or the culprit's description) is not explicitly stated, but can be confidently inferred from context clues, you MUST infer and guess it. If it is completely impossible to guess, output "Not specified".
Return ONLY valid JSON. Do not include markdown formatting, backticks, or conversational text.
Use these exact keys:
- Name
- Location
- Preferred way of contact
- Contact info
- Frequency of domestic violence
- Relationship with perpetrator
- Nature of domestic violence
- Severity of domestic violence
- Culprit details
- Other info

Incident Report:
"""
${resText}
"""`;

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GROQ_API_KEY.trim()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          { role: 'system', content: 'You output strictly valid JSON objects.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0,
        response_format: { type: 'json_object' }
      })
    });

    const data = await response.json();
    if (!response.ok) {
      console.error('Groq API Rejected Request:', data);
      return NextResponse.json({ error: 'Groq API Error' }, { status: 500 });
    }

    const result = data.choices[0]?.message?.content || '{}';

    return NextResponse.json({ decomposed: result });
  } catch (error: any) {
    console.error('Groq Decomposition Exception:', error.message);
    if (error.cause) console.error('Underlying cause:', error.cause);
    return NextResponse.json(
      { error: 'Failed to decompose text' },
      { status: 500 }
    );
  }
}
