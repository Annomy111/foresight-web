"""Super-Forecaster prompt templates for foresight analysis"""
from typing import Dict, Optional
from datetime import datetime

class PromptTemplates:
    """Container for prompt templates"""

    @staticmethod
    def get_super_forecaster_prompt(
        question: str,
        definition: str,
        timeframe: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Generate the Super-Forecaster prompt based on the research methodology

        Args:
            question: The main forecasting question
            definition: Operational definition of the event
            timeframe: Time period for the forecast
            additional_context: Any additional context to provide

        Returns:
            Formatted prompt string
        """
        prompt = f"""<System_Anweisung>
Du agierst als Experte für geopolitische Analyse und Prognostik, trainiert nach der Super-Forecasting-Methode. Deine Aufgabe ist es, eine präzise, quantifizierbare Wahrscheinlichkeitsprognose für die gestellte Frage zu liefern. Antworte als unvoreingenommener, datengestützter Analyst mit Zugang zu aktuellen Informationen.

**WICHTIG: Du hast Zugang zu aktuellen Informationen über das Internet. Nutze diesen Zugang, um die neuesten Entwicklungen zu recherchieren, bevor du deine Analyse beginnst.**
</System_Anweisung>

<Informationsbeschaffung>
Bevor du mit der eigentlichen Analyse beginnst, recherchiere die aktuellsten verfügbaren Informationen zu folgenden Bereichen:

1. **Aktuelle militärische Lage**: Neueste Entwicklungen an der Front, Winteroffensiven, Territorialveränderungen (Stand: Ende 2024/Anfang 2025)
2. **Diplomatische Entwicklungen**: Laufende Friedensverhandlungen, internationale Vermittlungsbemühungen, Positionen der Konfliktparteien
3. **Politische Faktoren**: Wahlergebnisse in relevanten Ländern (USA, Deutschland, andere), Regierungswechsel, Policy-Änderungen
4. **Wirtschaftliche Situation**: Aktuelle Sanktionen, Waffenlieferungen, Finanzhilfen, wirtschaftliche Belastung der Kriegsparteien
5. **Internationale Stakeholder**: Haltung von China, Indien, der EU, NATO, UN und anderen wichtigen Akteuren
6. **Kriegsmüdigkeit und öffentliche Meinung**: Aktuelle Umfragen in der Ukraine, Russland und Unterstützerländern

Integriere diese aktuellen Informationen systematisch in deine nachfolgende Analyse.
</Informationsbeschaffung>

<Aufgabenstellung>

<Frage>
{question}
</Frage>

<Definition>
{definition}
</Definition>

{f'<Zeitrahmen>{timeframe}</Zeitrahmen>' if timeframe else ''}

{f'<Zusätzlicher_Kontext>{additional_context}</Zusätzlicher_Kontext>' if additional_context else ''}

<Analyse_Anweisungen>
1. **Denke Schritt für Schritt (Chain of Thought):** Lege deine Überlegungen offen.

2. Führe eine Base Rate Analyse durch:
   - Identifiziere zunächst 10 Hauptattribute des Untersuchungsgegenstandes, die dafür maßgeblich sind, ob das Ereignis eintritt oder nicht. Beziehe dich dabei ausschließlich auf Attribute, die der Untersuchungsgegenstand schon besitzt. Nutze keine konditionalen Ereignisse, die erst noch eintreten müssten.

3. Ordne den Attributen eine Punktzahl zu bezogen auf ihre Wichtigkeit, wobei 0=unwichtig, 10=absolut entscheidend.

4. Finde mindestens 40 Fälle aus der Vergangenheit und weltweit, auf die diese Attribute zumindest teilweise zutreffen. Wenn du weniger Fälle findest, erfinde keine zusätzlichen, sondern fahre mit denen fort, die du hast.

5. Ordne diesen Fällen eine Punktzahl zu, welche die Erfüllung der genannten Attribute ausdrückt, mit 0=überhaupt nicht wie beim Untersuchungsgegenstand bis 10=exakt wie beim Untersuchungsgegenstand.

6. Berechne nun eine dritte Messgröße, die die Erfüllung der Attribute und deren unter 4. genannte Wichtigkeit einbezieht.

7. Untersuche nun, ob in den Fällen der Referenzklasse das Ereignis eingetreten ist, oder nicht.

8. Gib die Wahrscheinlichkeit, dass es eintrifft als Prozentzahl an, nutze dabei aber nicht das einfache arithmetische Mittel, sondern beziehe die Punktzahl aus 7. dabei ein, um diejenigen Fälle stärker zu gewichten, die besonders wichtige Attribute besonders stark erfüllen.

9. Dieses gewichtete Mittel ist deine Base Rate, die du nun weiter verwendest.

10. Schätze nun die Eintrittswahrscheinlichkeit in Prozent des Ereignisses ein ausschließlich aufgrund der Daten, die du über den Fall selbst kennst, also zunächst unter Ausschluss der Base Rate. Gehe dabei zunächst davon aus, dass du alle nötigen Informationen hast, und dass diese zuverlässig sind und dass das Ereignis einschätzbar ist. Diese Eintrittswahrscheinlichkeit ist die Case Rate.

11. Schätze nun in Prozent ein, wie hoch dein Vertrauen in deine Case Rate ist. Stütze dies auf:
    a) wie vollständig deine Informationen tatsächlich sind, gemessen daran, wieviele Informationen du eigentlich bräuchtest
    b) für wie glaubhaft du die dir vorliegenden Informationen hältst
    c) wie vorhersagbar ein solches Ereignis generell ist
    Die aggregierte Einschätzung aus diesen drei Faktoren in Prozent ist die Confidence.

12. Verrechne nun die Base Rate und die Case Rate und die Confidence nach folgender Formel und gib die finale Wahrscheinlichkeit des Ereigniseintritts aus:
    Final_Probability = (Base_Rate × (100 - Confidence) + Case_Rate × Confidence) / 100

</Analyse_Anweisungen>

<Ausgabeformat>
Gib deine Antwort ausschließlich im folgenden Format aus:

BEGRÜNDUNG:
[Hier fügst du deine vollständige Analyse gemäß den Anweisungen ein.]

PROGNOSE:
[Gib hier NUR die Prozentzahl an, z.B. "42%".]
</Ausgabeformat>

</Aufgabenstellung>"""
        return prompt

    @staticmethod
    def get_ukraine_ceasefire_prompt() -> str:
        """
        Get the specific Ukraine ceasefire 2026 prompt from the research document
        """
        question = "Mit welcher Wahrscheinlichkeit kommt es im Jahr 2026 zu einem Waffenstillstand in der Ukraine?"

        definition = """Ein 'Waffenstillstand' wird für dieses Experiment definiert als eine von beiden Konfliktparteien (Regierung der Ukraine und Regierung der Russischen Föderation) offiziell verkündete und für mindestens 30 aufeinanderfolgende Tage eingehaltene Einstellung aller Kampfhandlungen an allen Fronten. Der Beginn des 30-Tage-Zeitraums muss zwischen dem 1. Januar 2026, 00:00 Uhr, und dem 31. Dezember 2026, 23:59 Uhr Kiewer Zeit, liegen. Kleinere, lokale Scharmützel, die innerhalb von 24 Stunden beendet sind und von keiner der beiden Parteien als Beendigung des Waffenstillstands deklariert werden, gelten nicht als Bruch."""

        timeframe = "2026-01-01 bis 2026-12-31"

        return PromptTemplates.get_super_forecaster_prompt(
            question=question,
            definition=definition,
            timeframe=timeframe
        )

    @staticmethod
    def get_ukraine_ceasefire_enhanced_prompt() -> str:
        """
        Get the Enhanced Ukraine ceasefire 2026 prompt with ensemble reasoning capabilities
        """
        question = "Mit welcher Wahrscheinlichkeit kommt es im Jahr 2026 zu einem Waffenstillstand in der Ukraine?"

        definition = """Ein 'Waffenstillstand' wird für dieses Experiment definiert als eine von beiden Konfliktparteien (Regierung der Ukraine und Regierung der Russischen Föderation) offiziell verkündete und für mindestens 30 aufeinanderfolgende Tage eingehaltene Einstellung aller Kampfhandlungen an allen Fronten. Der Beginn des 30-Tage-Zeitraums muss zwischen dem 1. Januar 2026, 00:00 Uhr, und dem 31. Dezember 2026, 23:59 Uhr Kiewer Zeit, liegen. Kleinere, lokale Scharmützel, die innerhalb von 24 Stunden beendet sind und von keiner der beiden Parteien als Beendigung des Waffenstillstands deklariert werden, gelten nicht als Bruch."""

        timeframe = "2026-01-01 bis 2026-12-31"

        return PromptTemplates.get_ensemble_aware_super_forecaster_prompt(
            question=question,
            definition=definition,
            timeframe=timeframe
        )

    @staticmethod
    def get_ensemble_aware_super_forecaster_prompt(
        question: str,
        definition: str,
        timeframe: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Generate the Enhanced Ensemble-Aware Super-Forecaster prompt with meta-reasoning

        Based on 2024/2025 research on Meta Prompting, Confidence-Informed Self-Consistency (CISC),
        and Reasoning Topology-based Uncertainty Quantification.

        Args:
            question: The main forecasting question
            definition: Operational definition of the event
            timeframe: Time period for the forecast
            additional_context: Any additional context to provide

        Returns:
            Enhanced prompt string with ensemble reasoning capabilities
        """
        prompt = f"""<System_Anweisung>
Du agierst als Experte für geopolitische Analyse und Prognostik, trainiert nach der Super-Forecasting-Methode mit fortgeschrittenen Ensemble-Reasoning-Fähigkeiten. Deine Aufgabe ist es, eine präzise, quantifizierbare Wahrscheinlichkeitsprognose für die gestellte Frage zu liefern, die sowohl einzelne Analyse als auch meta-kognitive Selbstreflexion umfasst.

**WICHTIG: Du hast Zugang zu aktuellen Informationen über das Internet. Nutze diesen Zugang, um die neuesten Entwicklungen zu recherchieren, bevor du deine Analyse beginnst.**

**META-REASONING PRINZIPIEN:**
1. Führe kontinuierliche Selbstreflexion über deine eigenen kognitiven Biases und Unsicherheiten durch
2. Betrachte explizit alternative Perspektiven und Gegenfaktoren zu deiner Hauptanalyse
3. Quantifiziere deine Konfidenz für jeden Analyseschritt separat
4. Identifiziere potenzielle Outlier-Faktoren, die deine Einschätzung dramatisch ändern könnten
5. Praktiziere "Kalibrations-Bewusstsein" - bedenke Tendenzen zu Over- oder Underconfidence
</System_Anweisung>

<Informationsbeschaffung>
Bevor du mit der eigentlichen Analyse beginnst, recherchiere die aktuellsten verfügbaren Informationen zu folgenden Bereichen:

1. **Aktuelle militärische Lage**: Neueste Entwicklungen an der Front, Winteroffensiven, Territorialveränderungen (Stand: Ende 2024/Anfang 2025)
2. **Diplomatische Entwicklungen**: Laufende Friedensverhandlungen, internationale Vermittlungsbemühungen, Positionen der Konfliktparteien
3. **Politische Faktoren**: Wahlergebnisse in relevanten Ländern (USA, Deutschland, andere), Regierungswechsel, Policy-Änderungen
4. **Wirtschaftliche Situation**: Aktuelle Sanktionen, Waffenlieferungen, Finanzhilfen, wirtschaftliche Belastung der Kriegsparteien
5. **Internationale Stakeholder**: Haltung von China, Indien, der EU, NATO, UN und anderen wichtigen Akteuren
6. **Kriegsmüdigkeit und öffentliche Meinung**: Aktuelle Umfragen in der Ukraine, Russland und Unterstützerländern

Integriere diese aktuellen Informationen systematisch in deine nachfolgende Analyse.
</Informationsbeschaffung>

<Aufgabenstellung>

<Frage>
{question}
</Frage>

<Definition>
{definition}
</Definition>

{f'<Zeitrahmen>{timeframe}</Zeitrahmen>' if timeframe else ''}

{f'<Zusätzlicher_Kontext>{additional_context}</Zusätzlicher_Kontext>' if additional_context else ''}

<Ensemble_Analyse_Anweisungen>
**PHASE 1: HAUPTANALYSE (Standard Super-Forecaster Methode)**

1. **Denke Schritt für Schritt (Chain of Thought):** Lege deine Überlegungen offen.

2. Führe eine Base Rate Analyse durch:
   - Identifiziere zunächst 10 Hauptattribute des Untersuchungsgegenstandes, die dafür maßgeblich sind, ob das Ereignis eintritt oder nicht. Beziehe dich dabei ausschließlich auf Attribute, die der Untersuchungsgegenstand schon besitzt. Nutze keine konditionalen Ereignisse, die erst noch eintreten müssten.

3. Ordne den Attributen eine Punktzahl zu bezogen auf ihre Wichtigkeit, wobei 0=unwichtig, 10=absolut entscheidend.

4. Finde mindestens 40 Fälle aus der Vergangenheit und weltweit, auf die diese Attribute zumindest teilweise zutreffen. Wenn du weniger Fälle findest, erfinde keine zusätzlichen, sondern fahre mit denen fort, die du hast.

5. Ordne diesen Fällen eine Punktzahl zu, welche die Erfüllung der genannten Attribute ausdrückt, mit 0=überhaupt nicht wie beim Untersuchungsgegenstand bis 10=exakt wie beim Untersuchungsgegenstand.

6. Berechne nun eine dritte Messgröße, die die Erfüllung der Attribute und deren unter 4. genannte Wichtigkeit einbezieht.

7. Untersuche nun, ob in den Fällen der Referenzklasse das Ereignis eingetreten ist, oder nicht.

8. Gib die Wahrscheinlichkeit, dass es eintrifft als Prozentzahl an, nutze dabei aber nicht das einfache arithmetische Mittel, sondern beziehe die Punktzahl aus 7. dabei ein, um diejenigen Fälle stärker zu gewichten, die besonders wichtige Attribute besonders stark erfüllen.

9. Dieses gewichtete Mittel ist deine Base Rate, die du nun weiter verwendest.

10. Schätze nun die Eintrittswahrscheinlichkeit in Prozent des Ereignisses ein ausschließlich aufgrund der Daten, die du über den Fall selbst kennst, also zunächst unter Ausschluss der Base Rate. Gehe dabei zunächst davon aus, dass du alle nötigen Informationen hast, und dass diese zuverlässig sind und dass das Ereignis einschätzbar ist. Diese Eintrittswahrscheinlichkeit ist die Case Rate.

11. Schätze nun in Prozent ein, wie hoch dein Vertrauen in deine Case Rate ist. Stütze dies auf:
    a) wie vollständig deine Informationen tatsächlich sind, gemessen daran, wieviele Informationen du eigentlich bräuchtest
    b) für wie glaubhaft du die dir vorliegenden Informationen hältst
    c) wie vorhersagbar ein solches Ereignis generell ist
    Die aggregierte Einschätzung aus diesen drei Faktoren in Prozent ist die Confidence.

12. Verrechne nun die Base Rate und die Case Rate und die Confidence nach folgender Formel und gib die finale Wahrscheinlichkeit des Ereigniseintritts aus:
    Final_Probability = (Base_Rate × (100 - Confidence) + Case_Rate × Confidence) / 100

**PHASE 2: META-REASONING & SELBSTREFLEXION**

13. **Konfidenz-Analyse**: Bewerte deine Konfidenz in jeden der obigen Schritte separat (1-10 Skala). Identifiziere welche Schritte am unsichersten sind.

14. **Bias-Check**: Reflektiere explizit über mögliche kognitive Biases in deiner Analyse:
    - Verfügbarkeitsheuristik (übergewichtung leicht verfügbarer Informationen)
    - Bestätigungsfehler (bevorzugung bestätigender Evidenz)
    - Anker-Effekt (übermäßiger Einfluss früher Informationen)
    - Overconfidence-Bias (überschätzen der eigenen Genauigkeit)

15. **Alternative Perspektiven**: Entwickle bewusst 2-3 alternative Szenarien, die zu substantiell anderen Wahrscheinlichkeiten führen würden. Erkläre die Annahmen hinter jedem Szenario.

16. **Outlier-Analyse**: Identifiziere 3-5 Low-Probability/High-Impact Events, die deine Prognose dramatisch ändern könnten (Black Swan Events).

17. **Konsistenz-Prüfung**: Überprüfe die interne Konsistenz zwischen deiner Base Rate, Case Rate und Final Probability. Sind die Verhältnisse logisch nachvollziehbar?

**PHASE 3: KALIBRIERTE FINALE EINSCHÄTZUNG**

18. **Ensemble-Integration**: Berücksichtige deine Meta-Analyse und adjustiere deine Final_Probability entsprechend. Erkläre alle Anpassungen.

19. **Unsicherheits-Quantifizierung**: Gib einen Konfidenzbereich für deine finale Prognose an (z.B. 45% ± 8%).

20. **Qualitäts-Indikatoren**: Bewerte deine Gesamtanalyse auf:
    - Informationsvollständigkeit (1-10)
    - Analytische Rigorosität (1-10)
    - Bias-Resistenz (1-10)
    - Prognostische Konsistenz (1-10)
</Ensemble_Analyse_Anweisungen>

<Ausgabeformat>
Gib deine Antwort ausschließlich im folgenden erweiterten Format aus:

**HAUPTANALYSE:**
[Hier fügst du deine vollständige Analyse gemäß Schritten 1-12 ein.]

**META-REASONING:**
[Hier dokumentierst du deine Selbstreflexion gemäß Schritten 13-17.]

**FINALE KALIBRIERTE EINSCHÄTZUNG:**
[Hier führst du die finale Integration und Qualitätsbewertung durch (Schritte 18-20).]

**STRUKTURIERTE PROGNOSE:**

HAUPTPROGNOSE: [Gib hier NUR die Prozentzahl an, z.B. "42%".]

KONFIDENZBEREICH: [z.B. "42% ± 8%" oder "34% - 50%"]

SZENARIEN:
- Optimistisches Szenario: [Prozent]% (Wahrscheinlichkeit: [Prozent]%)
- Pessimistisches Szenario: [Prozent]% (Wahrscheinlichkeit: [Prozent]%)
- Outlier-Szenario: [Prozent]% (Wahrscheinlichkeit: [Prozent]%)

QUALITÄTSINDIKATOREN:
- Informationsvollständigkeit: [1-10]/10
- Analytische Rigorosität: [1-10]/10
- Bias-Resistenz: [1-10]/10
- Prognostische Konsistenz: [1-10]/10

KRITISCHE_UNSICHERHEITSFAKTOREN: [Liste der 3 wichtigsten Unsicherheiten]
</Ausgabeformat>

</Aufgabenstellung>"""
        return prompt

    @staticmethod
    def get_custom_forecast_prompt(
        question: str,
        definition: str,
        **kwargs
    ) -> str:
        """
        Create a custom forecast prompt with user-defined question and definition

        Args:
            question: The forecasting question
            definition: Operational definition of success criteria
            **kwargs: Additional parameters (timeframe, context)

        Returns:
            Formatted prompt
        """
        return PromptTemplates.get_super_forecaster_prompt(
            question=question,
            definition=definition,
            timeframe=kwargs.get('timeframe'),
            additional_context=kwargs.get('context')
        )

# Example usage patterns
class ForecastQuestions:
    """Pre-defined forecast questions for common scenarios"""

    UKRAINE_CEASEFIRE = {
        "id": "ukraine_ceasefire_2026",
        "title": "Ukraine Ceasefire Probability 2026",
        "question": "Mit welcher Wahrscheinlichkeit kommt es im Jahr 2026 zu einem Waffenstillstand in der Ukraine?",
        "definition": "Ein Waffenstillstand definiert als offizielle Verkündung und 30+ Tage Einhaltung",
        "category": "geopolitical",
        "timeframe": "2026"
    }

    @classmethod
    def get_all_questions(cls) -> Dict:
        """Get all pre-defined questions"""
        return {
            "ukraine_ceasefire": cls.UKRAINE_CEASEFIRE,
            # Add more pre-defined questions here
        }