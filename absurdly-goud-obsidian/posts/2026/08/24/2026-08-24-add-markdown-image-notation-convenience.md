Because I am using Obsidian to produce posts etc, I would prefer to create content using the Markdown syntax I know. I have now gotten it to play nice with Jekyll Includes Syntax

---more---

Jekyll requires a specific structure for includes docs:
```python
{% include image.html  
    src="image1.png"
    alt="Alt text 1"
    title="Alt text 1"
%}
```

Whereas the Markdown syntax is simpler: 
```markdown
![Alt text 1](image1.png)
```

With the changes brought into the `obsidian_to_jekyll` script, the conversion from Markdown Image Notation to Jekyll Includes Notation just works!