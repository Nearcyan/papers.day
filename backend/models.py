from django.db import models


class Author(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, db_index=True)
    affiliation = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    email = models.EmailField(null=True, blank=True)
    email_domain = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    citations = models.IntegerField(default=0, db_index=True)
    scholar_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    short_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name


class PaperImage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to="images")
    paper = models.ForeignKey("ArxivPaper", on_delete=models.CASCADE)


class PaperSource(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    content = models.TextField()
    paper = models.ForeignKey("ArxivPaper", on_delete=models.CASCADE)


class ArxivPaper(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    arxiv_id = models.CharField(max_length=20, unique=True)

    # fields scraped from the paper page:
    title = models.CharField(max_length=255, db_index=True)
    abstract = models.TextField(db_index=True)
    authors = models.ManyToManyField(Author)
    primary_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    subjects = models.ManyToManyField(Subject, related_name="papers")
    comment = models.TextField(null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    journal_ref = models.CharField(max_length=255, null=True, blank=True)
    publication_date = models.DateField()

    # fields we create
    summary = models.TextField(db_index=True)
    total_author_citations = models.IntegerField(default=0, db_index=True)
    citations = models.IntegerField(default=0, db_index=True)

    # file fields
    pdf = models.FileField(upload_to="pdfs", null=True, blank=True)
    screenshot = models.ImageField(upload_to="screenshots", null=True, blank=True)
    source_tar = models.FileField(upload_to="tar_sources", null=True, blank=True)
    images = models.ManyToManyField(PaperImage, related_name="paper_images")
    sources = models.ManyToManyField(PaperSource, related_name="paper_sources")

    def abstract_link(self) -> str:
        return f"https://arxiv.org/abs/{self.arxiv_id}"

    def pdf_link(self) -> str:
        return f"https://arxiv.org/pdf/{self.arxiv_id}.pdf"

    def source_link(self) -> str:
        return f"https://arxiv.org/e-print/{self.arxiv_id}"

    def __str__(self):
        return self.title
