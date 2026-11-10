"""Los bloques del prompt, uno por tema. Cada uno recibe la vista del mensaje (`PromptView`) y devuelve su texto, o "" si no aplica.

No deciden el orden ni los encabezados del prompt: eso lo hace `composer.py`.
"""
