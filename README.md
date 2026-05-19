# 🧠 IA Competitiva — Isolation

> Motor de busca adversarial para o jogo **Isolation**, com visualização interativa e documentação didática dos algoritmos de IA.

---

## 📌 Sobre o Projeto

Este projeto implementa e documenta uma **Inteligência Artificial** para o jogo Isolation, utilizando técnicas clássicas de busca adversarial. O objetivo é demonstrar, de forma visual e didática, como a IA toma decisões em jogos de dois jogadores.

O jogo Isolation é disputado em um tabuleiro **7 × 7**. A cada turno, o jogador move seu peão (como um rei do xadrez — uma casa em qualquer das 8 direções) e bloqueia uma célula do tabuleiro. Quem ficar sem movimentos, **perde**.

---

## 🎯 Algoritmos Implementados

| Algoritmo | Descrição | Complexidade |
|-----------|-----------|--------------|
| **Minimax** | Busca adversarial completa, alternando MAX (IA) e MIN (oponente) | O(b^d) |
| **Poda Alfa-Beta** | Minimax otimizado — elimina ramos que nunca serão escolhidos | O(b^(d/2)) |
| **Heurística Multi-componente** | Avaliação de estado com mobilidade, território, centralidade e isolamento (Chebyshev) | O(n) |

---

## 📁 Arquivos

```
jogoIA/
├── presentation.html   # Apresentação interativa dos algoritmos
└── explicacao.html     # Guia didático com exemplos do jogo
```

### `presentation.html`
Apresentação visual no estilo documentação técnica com:
- Tabuleiro 7×7 animado com movimentos do rei
- Árvore Minimax com caminho ótimo destacado
- Árvore Alfa-Beta com poda visual em vermelho
- Visualização da distância de Chebyshev
- Pseudocódigo com nomes de variáveis descritivos em português

### `explicacao.html`
Guia de estudo completo com:
- Analogias simples para entender cada algoritmo
- Exemplos reais de tabuleiros do Isolation
- Explicação **linha a linha** de cada função
- Comparativo Minimax vs Alfa-Beta com números reais

---

## 🔍 Função Heurística

A avaliação de cada estado do jogo combina **4 componentes**:

```
score = 2.5 × mobilidade
      + 1.2 × território
      + 0.8 × centralidade   ← usa distância de Chebyshev
      + 1.5 × isolamento      ← usa distância de Chebyshev
```

- **Mobilidade** — diferença entre movimentos disponíveis (meus − oponente)
- **Território** — células alcançáveis por cada jogador via flood fill (BFS)
- **Centralidade** — distância de Chebyshev do peão ao centro do tabuleiro
- **Isolamento** — distância de Chebyshev entre os dois peões

> **Distância de Chebyshev:** `d = max(|Δlinha|, |Δcoluna|)` — o número mínimo de passos que um rei precisa para ir de um ponto a outro.

---

## 🌲 Como o Minimax Funciona

```
Estado atual (tabuleiro)
        │
        ▼
   IA analisa todas as jogadas possíveis
        │
   Para cada jogada → simula o estado futuro
        │
   Oponente escolhe a pior jogada para a IA (MIN)
        │
   IA escolhe a melhor resposta (MAX)
        │
        ▼
   Melhor ação = aquela que garante o maior valor mínimo
```

### Exemplo de árvore com profundidade 2

```
         MAX = 3      ← IA escolhe o maior entre (3, 2)
        /       \
    MIN=3       MIN=2
   /  |  \     /  |  \
  3   7   4   5   9   2   ← valores da heurística
```

- MIN esquerdo: min(3, 7, 4) = **3**
- MIN direito: min(5, 9, 2) = **2**
- MAX raiz: max(3, 2) = **3** → IA vai pelo ramo esquerdo ✓

---

## ✂️ Poda Alfa-Beta

A poda elimina ramos que **nunca serão escolhidos**, tornando a busca até **2× mais profunda** no mesmo tempo.

```python
if beta <= alfa:
    break  # este ramo nunca será usado — para de explorar
```

| Métrica | Minimax | Alfa-Beta |
|---------|---------|-----------|
| Nós avaliados (d=5) | ~32.000 | ~180 |
| Profundidade em 150ms | 3 | 5–6 |
| Qualidade da decisão | ✓ | ✓ igual |

---

## 🕹️ Movimento no Tabuleiro

O peão se move como um **rei do xadrez** — uma casa em qualquer das 8 direções:

```
↖  ↑  ↗
←  ♚  →
↙  ↓  ↘
```

```python
DIRECOES_REI = [
    (-1,-1), (-1, 0), (-1,+1),   # cima-esq, cima, cima-dir
    ( 0,-1),          ( 0,+1),   # esquerda,       direita
    (+1,-1), (+1, 0), (+1,+1),   # baixo-esq, baixo, baixo-dir
]
```

---

## 🚀 Como Usar

1. Clone o repositório:
```bash
git clone https://github.com/Pauloj2/IA-Competitiva-.git
```

2. Abra os arquivos diretamente no navegador — nenhuma instalação necessária:
```
presentation.html  →  Apresentação visual dos algoritmos
explicacao.html    →  Guia didático linha a linha
```

---

## 🛠️ Tecnologias

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)

- HTML, CSS e JavaScript puros — sem dependências externas
- SVG para visualização das árvores de busca
- Design responsivo com tema dark

---

## 👨‍💻 Autor

**Paulo Junior** — Instituto Federal do Triângulo Mineiro (IFTM)

Disciplina: Inteligência Artificial e Computacional

---

## 📄 Licença

Este projeto é de uso acadêmico e educacional.
