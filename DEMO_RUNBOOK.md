# Demo runbook — Persian Site Assistant

## The story to tell

> راهکار نوین آریا یک شرکت کاملاً فرضی است. در این دمو، هشت محصول نرم‌افزاری ساختگی را در یک پایگاه دانش قرار داده‌ایم. دستیار نیاز مشتری را از متن پرسش استخراج می‌کند، محصولات مرتبط را از اسناد بازیابی می‌کند و گزینه مناسب را با دلیل، محدودیت و اسناد مرتبط پیشنهاد می‌دهد.

Be clear that the company, products, product IDs, project examples, and price ranges are fictional sample data.

## Suggested 4-minute walkthrough

### 1. Show the catalogue (30–45 seconds)

Open the products page and point out:

- Eight products, each with a stable product ID.
- Search and category filters.
- Different use cases and explicit exclusions.
- Price ranges marked as illustrative, not real quotations.

Then open the solutions page to show four example customer scenarios and their suggested products.

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

- پیگیر: customer/request records, owners, priorities, and status history.
- جریان‌کار: defined steps, routing, approvals, and repetitive workflows.

### 4. Show retrieval evidence and boundaries (45–60 seconds)

Ask:

```text
برای جست‌وجو در صدها PDF و پاسخ‌گویی به سؤال‌های کارکنان چه محصولی دارید؟
```

Expected recommendation: دانش‌یار (RNA-KNOW-07).

Point to the **اسناد مرتبط** cards. They show documents retrieved for the answer; they are not sentence-level citations.

Finally ask:

```text
شماره تلفن واقعی دفتر و نام مدیرعامل شرکت چیست؟
```

Expected behavior: the assistant should say this information is not defined rather than inventing it.

## What to explain technically

1. Source documents are stored as Markdown, text, and HTML under `data/raw/demo_company/`.
2. The ingestion pipeline normalizes Persian text and splits documents into overlapping chunks.
3. E5 converts those chunks into embeddings during the offline index build.
4. The vector store saves the embeddings and matching chunk metadata.
5. FastAPI embeds each question, retrieves relevant passages, and sends those passages to the configured OpenAI-compatible LLM API.
6. The model answers from the retrieved context; the website displays the related source documents separately.

The embedding model and retrieval index run locally. Only answer generation is sent to the configured LLM provider.

## Before leaving for the meeting

On the development PC:

1. Check that the E5 model files exist under `models/multilingual-e5-small/`.
2. Run the tests:
   `python -m pytest`
   `ruff check .`
3. Make sure Docker Desktop is running with Linux containers enabled.
4. Run the combined packaging script from PowerShell:
   `powershell -ExecutionPolicy Bypass -File .\scripts\package_demo.ps1`
5. Let it finish both builds and preflight checks. The native build must be created on Windows; the Docker preflight checks API readiness, the Nginx proxy, and the product page.
6. Copy the entire `release/demo/` folder to the USB drive. Keep a second copy on the development PC.

On the presentation PC:

- Copy the complete `demo` folder from the USB drive to a local drive.
- Double-click `START-DEMO.bat`.
- Choose Native Windows mode if Docker is unavailable, or Docker mode if Docker Desktop is installed and running with Linux containers.
- Have the LLM provider API key and exact model ID ready. The launcher asks for them; they are not stored in the USB folder.
- Keep the launcher window open while presenting. Press Enter in that window when the demo is finished.

The native option does not require Python or Docker Desktop on the presentation PC. The Docker option requires Docker Desktop. Both options require internet access to the LLM provider; the E5 embedding model and retrieval index are local.

## Honest limitations

- The company, catalogue, product IDs, scenarios, and sample prices are fictional.
- Recommendations are based on retrieved documents, not a live product database.
- The demo does not take payments, submit orders, or check live inventory.
- Source cards indicate related retrieved documents; the system does not guarantee sentence-level attribution.
- There is no user account system or conversation database in this MVP.
