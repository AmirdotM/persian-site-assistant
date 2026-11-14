# Demo runbook — Persian Site Assistant

## The story to tell

> راهکار نوین آریا یک شرکت کاملاً فرضی است. در این دمو، هشت محصول نرم‌افزاری ساختگی را در یک پایگاه دانش قرار داده‌ایم. دستیار نیاز مشتری را از متن پرسش استخراج می‌کند، محصولات مرتبط را از اسناد بازیابی می‌کند و گزینه مناسب را با دلیل، محدودیت و اسناد مرتبط پیشنهاد می‌دهد.

Keep saying **eight fictional products**, not eight real or commercially available products. All product IDs and price ranges are sample data created for this demonstration.

## Suggested 4-minute walkthrough

### 1. Show the catalogue (30–45 seconds)

Open `website/products.html`.

Point out:
- Eight distinct products, each with a product ID.
- Search and category filters.
- Different use cases and explicit exclusions.
- Price ranges marked as illustrative, not real quotations.

Then open `website/solutions.html` to show the four customer scenarios already mapped to primary and optional products.

### 2. Demonstrate a recommendation (60–90 seconds)

Ask the assistant:

```text
ما یک فروشگاه اینترنتی با حدود ۱۵۰ محصول داریم.
سفارش‌ها را دستی ثبت می‌کنیم و موجودی همیشه دقیق نیست.
بودجه نمایشی ما ۵۰ تا ۶۵ میلیون تومان است.
کدام محصول یا ترکیب محصولات مناسب‌تر است و چرا؟
```

Expected reasoning:
- بازارینو (RNA-SHOP-02) is the primary fit for the online catalogue, cart, and order workflow.
- انباربان (RNA-STOCK-05) is a separate complement if inventory movement and stock control are also required.
- Do not claim both products fit into the ۵۰–۶۵ million sample budget. Explain that the inventory component may need a later phase or separate budget.
- If a price is mentioned, explicitly call it a fictional demo range.

### 3. Show that it distinguishes similar products (45 seconds)

Ask:

```text
فروشگاه فعلی داریم و فقط کنترل ورود و خروج کالا و حداقل موجودی را لازم داریم؛ فروش آنلاین جدید نمی‌خواهیم. چه پیشنهادی دارید؟
```

Expected recommendation: انباربان, not بازارینو.

Then ask:

```text
تفاوت پیگیر و جریان‌کار چیست؟ برای تیمی که فقط درخواست‌های مشتری را ثبت و دنبال می‌کند کدام بهتر است؟
```

Expected distinction:
- پیگیر: customer/request records, owners, priorities, status history.
- جریان‌کار: defined steps, routing, approvals, and repetitive workflows.

### 4. Demonstrate the RAG evidence and boundaries (45–60 seconds)

Ask:

```text
برای جست‌وجو در صدها PDF و پاسخ‌گویی به سؤال‌های کارکنان چه محصولی دارید؟
```

Expected recommendation: دانش‌یار (RNA-KNOW-07).

Point to the **اسناد مرتبط** cards. These cards show retrieved documents related to the answer; they are not sentence-level citations. The model is instructed not to produce unstable numbered markers such as [S1].

Finally ask:

```text
شماره تلفن واقعی دفتر و نام مدیرعامل شرکت چیست؟
```

Expected behavior: state that this information is not defined, and do not invent it.

## What to explain technically

1. Documents are stored as Markdown under `data/raw/demo_company/`.
2. The ingestion pipeline normalizes Persian text, cleans Markdown, and creates chunks.
3. E5 converts the chunks into embeddings during the offline index build.
4. The vector store persists the embeddings and chunk metadata.
5. FastAPI embeds each question, retrieves the best matching passages, and sends those passages to the configured OpenAI-compatible LLM API.
6. The model answers from retrieved context; the UI separately displays one card per related source document.

## Before the meeting

- Rebuild the index after merging the product/catalogue changes:
  `python scripts/build_index.py`
- Verify the hosted LLM key, base URL, and model name in `.env`.
- Run the API and open `http://127.0.0.1:8000/ready`.
- Run `python scripts/smoke_test_api.py`; manually read the saved product-recommendation response.
- Keep `website/products.html` and `website/solutions.html` ready in browser tabs.
- If using Docker, test the portable package and start it once on the presentation machine before the meeting.

## Honest limitations to mention if asked

- The company, catalogue, product IDs, and sample prices are fictional.
- Recommendations are based on retrieved documents, not a live product database or transaction engine.
- This demo does not take payments, submit orders, or check live inventory.
- Source cards indicate related retrieved documents; the system does not guarantee sentence-level attribution.
- There is no authentication, conversation database, or distributed rate limiter in this MVP.
