import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  AudioLines,
  BadgeCheck,
  BookOpen,
  Camera,
  Check,
  CheckCircle2,
  Clock3,
  Download,
  FileText,
  Gauge,
  Hand,
  HeartPulse,
  History,
  Info,
  LoaderCircle,
  Pause,
  Play,
  Plus,
  RotateCcw,
  ScanFace,
  ShieldCheck,
  Trash2,
  TriangleAlert,
  Video,
  X,
  XCircle,
} from "lucide-react";

type Health = {
  status: string;
  model_available: boolean;
  model_loaded: boolean;
  model_error?: string | null;
  labels: string[];
  threshold: number;
};
type Prediction = {
  label: string;
  confidence: number;
  scores: Record<string, number>;
};
type DemoLog = {
  id: number;
  time: string;
  kind: "frame" | "prediction" | "system";
  title: string;
  detail: string;
  metadata?: Record<string, unknown>;
};
type Communication = {
  id: string;
  label: string;
  confidence: number;
  createdAt: string;
  note: string;
};
const defaultLabels = [
  "headache",
  "sore throat",
  "cough",
  "fever",
  "stomach aches",
  "tired",
  "runny nose",
  "nausea",
  "trouble breathing",
];
const FEATURES_PER_FRAME = 1662;
const symptomCopy: Record<string, string> = {
  headache: "Headache",
  "sore throat": "Sore throat",
  cough: "Cough",
  fever: "Fever",
  "stomach aches": "Stomach ache",
  tired: "Tiredness",
  "runny nose": "Runny nose",
  nausea: "Nausea",
  "trouble breathing": "Trouble breathing",
};
function titleCase(value: string) {
  return (
    symptomCopy[value] || value.replace(/\b\w/g, (char) => char.toUpperCase())
  );
}
function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const location = useLocation();
  useEffect(() => {
    const controller = new AbortController();
    fetch("http://127.0.0.1:8000/api/health", { signal: controller.signal })
      .then((response) => response.json())
      .then(setHealth)
      .catch(() => setHealth(null));
    const timer = window.setInterval(
      () =>
        fetch("http://127.0.0.1:8000/api/health")
          .then((r) => r.json())
          .then(setHealth)
          .catch(() => setHealth(null)),
      15000,
    );
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [location.pathname]);
  return (
    <div className="simple-app">
      <header className="simple-header">
        <Link className="simple-brand" to="/">
          <span className="simple-brand-mark"><Hand size={20} /></span>
          <span>MediSign <small>DEMO</small></span>
        </Link>
        <nav className="simple-nav" aria-label="Main navigation">
          <NavLink to="/" end>Camera</NavLink>
          <NavLink to="/instructions">Sign guide</NavLink>
        </nav>
        <span className={`simple-model-status ${health?.model_available ? "is-ready" : ""}`}>
          <span className="status-dot" />
          {health?.model_available ? "Model ready" : "Model offline"}
        </span>
      </header>
      <main className="simple-main">
        <Routes>
          <Route path="/" element={<Recognition health={health} />} />
          <Route path="/instructions" element={<Instructions />} />
          <Route path="*" element={<Recognition health={health} />} />
        </Routes>
      </main>
      <footer className="simple-footer">
        Demo only · A symptom suggestion is not a medical diagnosis.
      </footer>
    </div>
  );
}

function Instructions() {
  const signs = [
    ["Headache", "headache.gif"],
    ["Sore throat", "sore_throat.gif"],
    ["Cough", "cough.gif"],
    ["Fever", "fever.gif"],
    ["Stomach aches", "stomache_aches.gif"],
    ["Tired", "tired.gif"],
    ["Runny nose", "runny_nose.gif"],
    ["Nausea", "nausea.gif"],
    ["Trouble breathing", "trouble_breathing.gif"],
  ];
  return (
    <section className="guide-page">
      <div className="guide-heading">
        <span className="guide-kicker">QUICK GUIDE</span>
        <h1>Signs in this demo</h1>
        <p>Watch a sign example, then try it in front of the camera.</p>
      </div>
      <div className="guide-note">
        <Info size={18} />
        <p>Face the camera with your upper body and hands visible. Sign one symptom at a time, at a comfortable pace, then wait for the result beside the camera.</p>
      </div>
      <div className="guide-clips">
        {signs.map(([label, file]) => (
          <figure className="guide-clip" key={file}>
            <img
              src={`https://sign-language-translator.onrender.com/imgs/${file}`}
              alt={`${label} sign example`}
              loading="lazy"
            />
            <figcaption>{label}</figcaption>
          </figure>
        ))}
      </div>
      <p className="guide-source">Animated examples from the <a href="https://sign-language-translator.onrender.com/#instructions" target="_blank" rel="noreferrer">original sign language demo</a>.</p>
      <Link to="/" className="button button-primary guide-start"><Camera size={17} /> Open camera</Link>
      <p className="guide-caveat">This is a small demonstration vocabulary. Results can be wrong and should not be used for medical decisions.</p>
    </section>
  );
}

export function PageHeading({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}
export function Dashboard({
  health,
  history,
}: {
  health: Health | null;
  history: Communication[];
}) {
  return (
    <>
      <PageHeading
        eyebrow="OVERVIEW"
        title="A clearer way to be heard."
        subtitle="Turn a signed symptom into a patient-confirmed message for the care team."
        action={
          <Link to="/recognize" className="button button-primary">
            <ScanFace size={17} /> Start recognition <ArrowRight size={16} />
          </Link>
        }
      />
      <div className="welcome-banner">
        <div className="welcome-icon">
          <Hand size={24} />
        </div>
        <div className="welcome-copy">
          <span className="welcome-kicker">PATIENT COMMUNICATION · ASL</span>
          <h2>Communication, with the patient in control.</h2>
          <p>
            MediSign recognises nine symptom signs. Every suggestion is reviewed
            and confirmed by the patient before it becomes a message.
          </p>
          <Link to="/recognize" className="text-link">
            Open sign recognition <ArrowRight size={15} />
          </Link>
        </div>
        <div className="banner-orbit orbit-one" />
        <div className="banner-orbit orbit-two" />
      </div>
      <div className="section-heading">
        <div>
          <h2>Workspace at a glance</h2>
          <p>System status and recent patient communication.</p>
        </div>
        <span className="section-caption">LOCAL SESSION</span>
      </div>
      <div className="stat-grid">
        <Stat
          icon={Hand}
          tone="blue"
          label="Supported symptoms"
          value="09"
          detail="ASL symptom vocabulary"
        />
        <Stat
          icon={BadgeCheck}
          tone="green"
          label="Confirmed messages"
          value={String(history.length).padStart(2, "0")}
          detail="This browser only"
        />
        <Stat
          icon={Gauge}
          tone="amber"
          label="Recognition model"
          value={health?.model_available ? "Ready" : "Not trained"}
          detail={
            health?.model_available
              ? "Local model checkpoint found"
              : "Train to enable recognition"
          }
        />
      </div>
      <div className="dashboard-grid">
        <section className="panel recent-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent confirmed messages</h3>
              <p>Only patient-approved results appear here.</p>
            </div>
            <Link className="quiet-link" to="/communications">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          {history.length === 0 ? (
            <EmptyState
              icon={History}
              title="No communications yet"
              text="Confirmed patient messages will appear here."
              action={
                <Link
                  className="button button-secondary button-small"
                  to="/recognize"
                >
                  <Plus size={15} /> New communication
                </Link>
              }
            />
          ) : (
            <div className="recent-list">
              {history.slice(0, 4).map((item) => (
                <CommunicationRow key={item.id} item={item} />
              ))}
            </div>
          )}
        </section>
        <section className="panel readiness-panel">
          <div className="panel-heading">
            <div>
              <h3>System readiness</h3>
              <p>Local services for this session.</p>
            </div>
            <span
              className={`readiness-badge ${health?.status === "ok" ? "ready" : ""}`}
            >
              <span className="status-dot" />
              {health?.status === "ok" ? "Connected" : "Offline"}
            </span>
          </div>
          <div className="readiness-rows">
            <ReadinessRow
              icon={Activity}
              label="Inference service"
              value={health?.status === "ok" ? "Online" : "Unavailable"}
              ok={health?.status === "ok"}
            />
            <ReadinessRow
              icon={Gauge}
              label="Trained model"
              value={
                health?.model_available ? "Available" : "Checkpoint missing"
              }
              ok={Boolean(health?.model_available)}
            />
            <ReadinessRow
              icon={Video}
              label="Camera access"
              value="Requested when needed"
              ok={null}
            />
          </div>
          <div className="readiness-note">
            <Info size={15} />
            <span>
              Model confidence is an estimate from the trained model, not a
              medically validated probability.
            </span>
          </div>
        </section>
      </div>
      <div className="disclaimer-strip">
        <TriangleAlert size={17} />
        <span>
          <strong>Assistive communication only.</strong> MediSign does not
          diagnose conditions or replace professional medical assessment.
        </span>
        <Link to="/about">
          Learn about limitations <ArrowRight size={14} />
        </Link>
      </div>
    </>
  );
}
function Stat({
  icon: Icon,
  tone,
  label,
  value,
  detail,
}: {
  icon: typeof Hand;
  tone: string;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>
        <Icon size={18} />
      </div>
      <span className="stat-label">{label}</span>
      <strong
        className={`stat-value ${value === "Ready" ? "value-ready" : ""}`}
      >
        {value}
      </strong>
      <span className="stat-detail">{detail}</span>
    </div>
  );
}
function ReadinessRow({
  icon: Icon,
  label,
  value,
  ok,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
  ok: boolean | null;
}) {
  return (
    <div className="readiness-row">
      <span className="readiness-icon">
        <Icon size={16} />
      </span>
      <span>{label}</span>
      <strong
        className={
          ok === true ? "text-green" : ok === false ? "text-muted" : ""
        }
      >
        {ok === true && <CheckCircle2 size={14} />} {value}
      </strong>
    </div>
  );
}
function CommunicationRow({ item }: { item: Communication }) {
  return (
    <div className="communication-row">
      <div className="symptom-mark">
        <HeartPulse size={17} />
      </div>
      <div className="communication-copy">
        <strong>Patient reports {article(item.label)}.</strong>
        <span>
          <Clock3 size={13} />
          {formatDate(item.createdAt)}
        </span>
      </div>
      <span className="confirmed-tag">
        <Check size={13} /> Confirmed
      </span>
    </div>
  );
}
function article(label: string) {
  const phrases: Record<string, string> = {
    headache: "a headache",
    "sore throat": "a sore throat",
    cough: "a cough",
    fever: "a fever",
    "stomach aches": "stomach aches",
    tired: "feeling tired",
    "runny nose": "a runny nose",
    nausea: "nausea",
    "trouble breathing": "trouble breathing",
  };
  return `experiencing ${phrases[label] || titleCase(label).toLowerCase()}`;
}
function EmptyState({
  icon: Icon,
  title,
  text,
  action,
}: {
  icon: typeof History;
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Icon size={20} />
      </div>
      <strong>{title}</strong>
      <p>{text}</p>
      {action}
    </div>
  );
}

function Recognition({ health }: { health: Health | null }) {
  const videoRef = useRef<HTMLVideoElement>(null),
    canvasRef = useRef<HTMLCanvasElement>(null),
    cameraRef = useRef<MediaStream | null>(null),
    holisticRef = useRef<any>(null),
    rafRef = useRef(0),
    busyRef = useRef(false),
    previousVideoTime = useRef(-1),
    frameCount = useRef(0),
    inferenceCount = useRef(0),
    sessionId = useRef(0),
    lastHandFeatures = useRef<number[] | null>(null),
    sequence = useRef<number[][]>([]),
    votes = useRef<Prediction[]>([]);
  const [cameraState, setCameraState] = useState<
      "idle" | "starting" | "ready" | "error"
    >("idle"),
    [cameraError, setCameraError] = useState(""),
    [running, setRunning] = useState(false),
    [progress, setProgress] = useState(0),
    [processedFrames, setProcessedFrames] = useState(0),
    [predictionRuns, setPredictionRuns] = useState(0),
    [prediction, setPrediction] = useState<Prediction | null>(null),
    [candidate, setCandidate] = useState<Prediction | null>(null),
    [processStatus, setProcessStatus] = useState("Waiting to start"),
    [demoLog, setDemoLog] = useState<DemoLog[]>([]),
    [expectedLabel, setExpectedLabel] = useState(""),
    [uncertain, setUncertain] = useState(false),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const threshold = health?.threshold ?? 0.65;
  const appendLog = useCallback((entry: Omit<DemoLog, "id" | "time">) => {
    setDemoLog((current) => [
      { ...entry, id: Date.now() + Math.random(), time: new Date().toLocaleTimeString() },
      ...current,
    ].slice(0, 300));
  }, []);
  const stopCamera = useCallback(() => {
    sessionId.current += 1;
    cancelAnimationFrame(rafRef.current);
    cameraRef.current?.getTracks().forEach((track) => track.stop());
    cameraRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    void holisticRef.current?.close?.();
    holisticRef.current = null;
    setRunning(false);
    setCameraState("idle");
    busyRef.current = false;
    setBusy(false);
    setProcessStatus("Camera stopped. Session log remains available until cleared.");
    appendLog({ kind: "system", title: "Camera stopped", detail: "No new frames are being captured." });
  }, [appendLog]);
  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas)
      canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }, []);
  const reset = useCallback(() => {
    sessionId.current += 1;
    sequence.current = [];
    votes.current = [];
    frameCount.current = 0;
    inferenceCount.current = 0;
    lastHandFeatures.current = null;
    setProgress(0);
    setProcessedFrames(0);
    setPredictionRuns(0);
    setPrediction(null);
    setCandidate(null);
    setDemoLog([]);
    setProcessStatus("Waiting to start");
    setUncertain(false);
    setNotice("");
    setBusy(false);
    busyRef.current = false;
    clearCanvas();
  }, [clearCanvas]);
  const infer = useCallback(
    async (frames: number[][], sourceFrame: number, currentSession: number) => {
      busyRef.current = true;
      setBusy(true);
      setProcessStatus("Sending the latest 30-frame window to the model…");
      const startedAt = performance.now();
      try {
        const response = await fetch("http://127.0.0.1:8000/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sequence: frames }),
        });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || "Model inference failed.");
        }
        const result = (await response.json()) as Prediction;
        if (currentSession !== sessionId.current) return;
        const elapsed = performance.now() - startedAt;
        inferenceCount.current += 1;
        setPredictionRuns(inferenceCount.current);
        setCandidate(result);
        votes.current = [...votes.current, result].slice(-5);
        const counts = new Map<string, Prediction[]>();
        votes.current.forEach((item) =>
          counts.set(item.label, [...(counts.get(item.label) || []), item]),
        );
        const stable = [...counts.values()].sort(
          (a, b) => b.length - a.length,
        )[0];
        if (
          stable.length >= 3 &&
          stable[stable.length - 1].confidence >= threshold
        ) {
          setPrediction(stable[stable.length - 1]);
          setUncertain(false);
          setNotice("");
          setProcessStatus(`Stable result: ${titleCase(stable[stable.length - 1].label)} (${stable.length}/5 recent predictions agree).`);
        } else if (result.confidence < threshold && votes.current.length >= 3) {
          setPrediction(null);
          setUncertain(true);
          setProcessStatus("Low confidence. Waiting for a clearer or more consistent sign.");
        } else {
          setProcessStatus(`Checking consistency: ${titleCase(result.label)} is the current guess (${stable.length}/5 agree).`);
        }
        const topScores = Object.entries(result.scores)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([label, score]) => `${titleCase(label)} ${Math.round(score * 100)}%`)
          .join(" · ");
        appendLog({
          kind: "prediction",
          title: `Prediction ${inferenceCount.current} · frame ${sourceFrame}`,
          detail: `${topScores} · ${elapsed.toFixed(0)} ms round trip${stable.length >= 3 ? ` · ${stable.length}/5 agree` : ""}`,
          metadata: {
            prediction_number: inferenceCount.current,
            source_frame: sourceFrame,
            window_start_frame: Math.max(1, sourceFrame - 29),
            window_end_frame: sourceFrame,
            top_scores: Object.fromEntries(Object.entries(result.scores).sort((a, b) => b[1] - a[1]).slice(0, 3)),
            confidence: result.confidence,
            request_round_trip_ms: Number(elapsed.toFixed(2)),
            agreement_label: stable[0]?.label ?? null,
            agreement_count: stable.length,
            confidence_threshold: threshold,
          },
        });
      } catch (error) {
        if (currentSession !== sessionId.current) return;
        const message = error instanceof Error ? error.message : "Could not run inference.";
        setNotice(message);
        setProcessStatus("Prediction request failed. Check that the local model service is running.");
        appendLog({ kind: "system", title: "Prediction error", detail: message });
      } finally {
        if (currentSession === sessionId.current) {
          busyRef.current = false;
          setBusy(false);
        }
      }
    },
    [appendLog, threshold],
  );
  const start = useCallback(async () => {
    if (!health?.model_available) {
      setNotice(
        "A trained model checkpoint is required before recognition can start.",
      );
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraState("error");
      setCameraError(
        "Camera access requires localhost or a secure browser context.",
      );
      return;
    }
    setCameraState("starting");
    setCameraError("");
    setNotice("");
    reset();
    setProcessStatus("Requesting camera and loading the landmark detector…");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });
      cameraRef.current = stream;
      if (!videoRef.current) throw new Error("Camera preview is unavailable.");
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      const { Holistic } = await import("@mediapipe/holistic");
      const model = new Holistic({
        locateFile: (file: string) => `/mediapipe/${file}`,
      });
      model.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        refineFaceLandmarks: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });
      model.onResults((result: any) => {
        const finiteValue = (value: unknown) =>
          typeof value === "number" && Number.isFinite(value) ? value : 0;
        const pointValues = (
          points: any[] | undefined,
          count: number,
          visibility: boolean,
        ) => {
          const dimensions = visibility ? 4 : 3;
          if (!points?.length) return Array(count * dimensions).fill(0);
          return points.flatMap((point: any) =>
            visibility
              ? [finiteValue(point.x), finiteValue(point.y), finiteValue(point.z), finiteValue(point.visibility ?? 0)]
              : [finiteValue(point.x), finiteValue(point.y), finiteValue(point.z)],
          );
        };
        const features = [
          ...pointValues(result.poseLandmarks, 33, true),
          ...pointValues(result.faceLandmarks, 468, false),
          ...pointValues(result.leftHandLandmarks, 21, false),
          ...pointValues(result.rightHandLandmarks, 21, false),
        ];
        if (features.length !== FEATURES_PER_FRAME) {
          setProcessStatus(`Frame rejected: expected ${FEATURES_PER_FRAME} values, got ${features.length}.`);
          appendLog({
            kind: "system",
            title: `Frame ${frameCount.current + 1} rejected`,
            detail: `Landmark feature length was ${features.length}; expected ${FEATURES_PER_FRAME}. No prediction was sent.`,
            metadata: { feature_count: features.length, expected_feature_count: FEATURES_PER_FRAME },
          });
          return;
        }
        sequence.current = [...sequence.current, features].slice(-30);
        frameCount.current += 1;
        const frameNumber = frameCount.current;
        if (frameNumber <= 30 || frameNumber % 5 === 0) {
          setProgress(sequence.current.length);
          setProcessedFrames(frameNumber);
          if (!busyRef.current) {
            setProcessStatus(
              sequence.current.length < 30
                ? `Capturing warm-up window: ${sequence.current.length}/30 frames.`
                : `Live capture · frame ${frameNumber} · updating the rolling window.`,
            );
          }
        }
        const leftHand = result.leftHandLandmarks;
        const rightHand = result.rightHandLandmarks;
        const handFeatures = features.slice(1536);
        const handsVisible = Boolean(leftHand?.length || rightHand?.length);
        const motion = handsVisible && lastHandFeatures.current
          ? handFeatures.reduce((sum, value, index) => sum + Math.abs(value - lastHandFeatures.current![index]), 0) / handFeatures.length
          : null;
        lastHandFeatures.current = handFeatures;
        if (frameNumber % 5 === 0) {
          const visible = [
            result.poseLandmarks?.length ? "upper body" : null,
            result.faceLandmarks?.length ? "face" : null,
            leftHand?.length ? "left hand" : null,
            rightHand?.length ? "right hand" : null,
          ].filter(Boolean);
          appendLog({
            kind: "frame",
            title: `Frame ${frameNumber} captured`,
            detail: `${visible.length ? visible.join(" · ") : "No landmarks detected"}${motion === null ? "" : ` · hand movement ${motion.toFixed(3)}`}`,
            metadata: {
              frame_number: frameNumber,
              pose_detected: Boolean(result.poseLandmarks?.length),
              face_detected: Boolean(result.faceLandmarks?.length),
              left_hand_detected: Boolean(leftHand?.length),
              right_hand_detected: Boolean(rightHand?.length),
              feature_count: features.length,
              finite_features: features.every(Number.isFinite),
              mean_hand_coordinate_change: motion,
              rolling_window_frames: sequence.current.length,
            },
          });
        }
        const canvas = canvasRef.current,
          video = videoRef.current;
        if (canvas && video) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext("2d");
          ctx?.clearRect(0, 0, canvas.width, canvas.height);
          if (ctx) {
            const drawPoints = (points: any[] | undefined, color: string) =>
              points?.forEach((point: any) => {
                ctx.beginPath();
                ctx.arc(
                  point.x * canvas.width,
                  point.y * canvas.height,
                  2,
                  0,
                  Math.PI * 2,
                );
                ctx.fillStyle = color;
                ctx.fill();
              });
            drawPoints(result.poseLandmarks, "#93c5fd");
            drawPoints(result.leftHandLandmarks, "#46c8aa");
            drawPoints(result.rightHandLandmarks, "#46c8aa");
            drawPoints(
              result.faceLandmarks?.filter(
                (_: any, index: number) => index % 5 === 0,
              ),
              "#a5b4fc",
            );
          }
        }
        if (
          sequence.current.length === 30 &&
          frameCount.current % 10 === 0 &&
          !busyRef.current
        )
          void infer([...sequence.current], frameNumber, sessionId.current);
      });
      holisticRef.current = model;
      setCameraState("ready");
      setRunning(true);
      setProcessStatus("Landmark detector ready. Capturing the first 30 frames…");
      appendLog({ kind: "system", title: "Camera started", detail: "Processing happens in this browser; camera video is not saved." });
      const tick = async () => {
        const video = videoRef.current;
        if (!video || !cameraRef.current) return;
        if (
          video.readyState >= 2 &&
          video.currentTime !== previousVideoTime.current
        ) {
          previousVideoTime.current = video.currentTime;
          try {
            await model.send({ image: video });
          } catch (error) {
            setNotice(
              error instanceof Error
                ? error.message
                : "Landmark processing failed.",
            );
          }
        }
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch (error) {
      cameraRef.current?.getTracks().forEach((track) => track.stop());
      cameraRef.current = null;
      setCameraState("error");
      setCameraError(
        error instanceof Error
          ? error.message
          : "Could not start the camera. Check browser permissions and network access for the landmark model.",
      );
    }
  }, [appendLog, health?.model_available, infer, reset]);
  const togglePause = useCallback(() => {
    if (!cameraRef.current) return;
    const next = !running;
    cameraRef.current.getVideoTracks().forEach((track) => {
      track.enabled = next;
    });
    setRunning(next);
    if (!next) {
      setProcessStatus("Capture paused. Resume to continue live predictions.");
      appendLog({ kind: "system", title: "Capture paused", detail: "The current prediction log is kept for this session." });
      cancelAnimationFrame(rafRef.current);
      return;
    }
    setProcessStatus("Capture resumed. Updating the rolling window…");
    appendLog({ kind: "system", title: "Capture resumed", detail: "New frames will be analyzed continuously." });
    const tick = async () => {
      const video = videoRef.current;
      if (
        !video ||
        !cameraRef.current ||
        !cameraRef.current.getVideoTracks()[0]?.enabled
      )
        return;
      if (
        video.readyState >= 2 &&
        video.currentTime !== previousVideoTime.current
      ) {
        previousVideoTime.current = video.currentTime;
        try {
          await holisticRef.current?.send({ image: video });
        } catch (error) {
          setNotice(
            error instanceof Error
              ? error.message
              : "Landmark processing failed.",
          );
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [appendLog, running]);
  const downloadLog = useCallback(() => {
    const payload = {
      project: "MediSign ASL symptom demo",
      expected_sign: expectedLabel || null,
      exported_at: new Date().toISOString(),
      settings: {
        rolling_window_frames: 30,
        prediction_interval_frames: 10,
        confidence_threshold: threshold,
      },
      note: "Frame entries contain landmark-presence metadata only. Camera images and raw landmark arrays are not included.",
      entries: demoLog,
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `medisign-session-${new Date().toISOString().replace(/:/g, "-")}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [demoLog, expectedLabel, threshold]);
  useEffect(
    () => () => {
      cancelAnimationFrame(rafRef.current);
      cameraRef.current?.getTracks().forEach((track) => track.stop());
      void holisticRef.current?.close?.();
    },
    [],
  );
  return (
    <section className="demo-page">
      <div className="demo-heading">
        <div>
          <span className="guide-kicker">LIVE CAMERA DEMO</span>
          <h1>Show a symptom sign</h1>
          <p>Start the camera, sign one symptom, and see the model’s suggestion.</p>
        </div>
        <Link className="demo-guide-link" to="/instructions"><BookOpen size={16} /> Sign guide</Link>
      </div>
      {!health?.model_available && (
        <div className="simple-alert">
          <TriangleAlert size={17} />
          <span>
            <strong>Model not available.</strong> Start the local API with the trained model to enable recognition.
          </span>
        </div>
      )}
      <div className="recognition-layout">
        <section className="panel camera-panel">
          <div className="panel-heading camera-panel-heading">
            <div>
              <h3>Camera</h3>
              <p>Keep your face, hands, and upper body in view.</p>
            </div>
            <span
              className={`camera-status ${cameraState === "ready" ? "camera-live" : ""}`}
            >
              <span className="status-dot" />
              {cameraState === "ready"
                ? running
                  ? "Live"
                  : "Paused"
                : cameraState === "starting"
                  ? "Starting"
                  : "Camera off"}
            </span>
          </div>
          <div
            className={`video-stage ${cameraState === "ready" ? "video-active" : ""}`}
          >
            <video ref={videoRef} autoPlay muted playsInline />
            <canvas
              ref={canvasRef}
              className="landmark-canvas"
            />
            {cameraState !== "ready" && (
              <div className="camera-placeholder">
                <div className="camera-placeholder-icon">
                  {cameraState === "starting" ? (
                    <LoaderCircle className="spin" size={27} />
                  ) : (
                    <Camera size={26} />
                  )}
                </div>
                <strong>
                  {cameraState === "starting"
                    ? "Preparing your camera"
                    : cameraState === "error"
                      ? "Camera unavailable"
                      : "Your camera preview will appear here"}
                </strong>
                <p>
                  {cameraState === "error"
                    ? cameraError
                    : "Your video is processed locally and is never saved."}
                </p>
              </div>
            )}
            <span className="camera-corner corner-tl" />
            <span className="camera-corner corner-tr" />
            <span className="camera-corner corner-bl" />
            <span className="camera-corner corner-br" />
            {cameraState === "ready" && (
              <span
                className={`recording-indicator ${running ? "" : "paused"}`}
              >
                <span className="status-dot" />
                {running ? "ANALYSING" : "PAUSED"}
              </span>
            )}
          </div>
          <div className="camera-toolbar">
            <span className="toolbar-note"><ShieldCheck size={14} /> Camera video is not saved</span>
          </div>
          {cameraState === "error" && (
            <div className="camera-error">
              <TriangleAlert size={15} />
              {cameraError}
            </div>
          )}
          <div className="camera-controls">
            {cameraState !== "ready" ? (
              <button
                className="button button-primary"
                onClick={() => void start()}
                disabled={
                  cameraState === "starting" || !health?.model_available
                }
              >
                {cameraState === "starting" ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Camera size={17} />
                )}{" "}
                {cameraState === "starting" ? "Preparing…" : "Start camera"}
              </button>
            ) : (
              <>
                <button className="button button-primary" onClick={togglePause}>
                  {running ? <Pause size={16} /> : <Play size={16} />}{" "}
                  {running ? "Pause" : "Resume"}
                </button>
                <button className="button button-secondary" onClick={reset}>
                  <RotateCcw size={16} /> Start over
                </button>
                <button
                  className="icon-button stop-button"
                  onClick={stopCamera}
                  aria-label="Stop camera"
                >
                  <X size={17} />
                </button>
              </>
            )}
            <div className="sequence-progress">
              <div className="progress-label">
                <span>Rolling frame window</span>
                <strong>
                  {progress}
                  <small> / 30 · {processedFrames} captured</small>
                </strong>
              </div>
              <div className="progress-track">
                <div style={{ width: `${(progress / 30) * 100}%` }} />
              </div>
            </div>
          </div>
        </section>
        <div className="recognition-side">
          <section
            className={`panel result-panel ${prediction ? "has-prediction" : ""}`}
          >
            <div className="panel-heading">
              <div>
                <h3>Detected symptom</h3>
                <p>{prediction ? "Most recent stable model result" : "Waiting for a stable model result"}</p>
              </div>
              <span className="result-icon">
                <ScanFace size={18} />
              </span>
            </div>
            <div className={`process-status ${busy ? "is-working" : ""}`} role="status" aria-live="polite">
              <span className="process-status-dot" />
              <div>
                <strong>{busy ? "Predicting now" : "What the system is doing"}</strong>
                <p>{processStatus}</p>
                <small>{processedFrames} frames processed · {predictionRuns} model checks · checks about every 10 frames when ready</small>
              </div>
            </div>
            {candidate && (
              <div className="live-candidate">
                <span>Latest window guess</span>
                <strong>{titleCase(candidate.label)}</strong>
                <b>{Math.round(candidate.confidence * 100)}%</b>
              </div>
            )}
            {prediction ? (
              <>
                <h2 className="result-symptom">
                  {titleCase(prediction.label)}
                </h2>
                <div className="confidence-line">
                  <span>Model confidence</span>
                  <strong>{Math.round(prediction.confidence * 100)}%</strong>
                </div>
                <div className="confidence-track">
                  <div style={{ width: `${prediction.confidence * 100}%` }} />
                </div>
                <p className="confidence-note"><Info size={14} /> Demo estimate only; it may be incorrect.</p>
                <button className="button button-secondary result-retry" onClick={reset}><RotateCcw size={15} /> Clear result</button>
              </>
            ) : (
              <div className="result-empty">
                <div className="scan-orbit">
                  <div className="scan-core">
                    <ScanFace size={22} />
                  </div>
                  <span />
                  <span />
                  <span />
                </div>
                <strong>
                  {uncertain
                    ? "Unable to recognise sign"
                    : busy
                      ? "Reviewing sign…"
                      : cameraState === "ready"
                          ? "Listening for a sign"
                        : "Ready when you are"}
                </strong>
                <p>
                  {uncertain
                    ? "The current sign was not clear enough. Try a slower, clearer sign."
                    : busy
                      ? "A complete sequence is being checked by the local model."
                      : cameraState === "ready"
                        ? "Sign a supported symptom and hold it in frame."
                        : "Start camera to begin."}
                </p>
              </div>
            )}
            {(busy || notice) && (
              <div
                className={`inference-status ${notice ? "notice-status" : ""}`}
              >
                {busy ? (
                  <LoaderCircle className="spin" size={15} />
                ) : notice.includes("confirmed") ? (
                  <CheckCircle2 size={15} />
                ) : (
                  <Info size={15} />
                )}{" "}
                {notice || "Running local model inference…"}
              </div>
            )}
          </section>
          <section className="panel session-log" aria-label="Recent session activity">
            <div className="session-log-heading">
              <div>
                <h3>Recent activity</h3>
                <p>Latest predictions and session updates.</p>
              </div>
              <div className="session-log-actions">
                <label className="expected-sign-picker">Test sign
                  <select value={expectedLabel} onChange={(event) => setExpectedLabel(event.target.value)}>
                    <option value="">Choose label</option>
                    {defaultLabels.map((label) => <option key={label} value={label}>{titleCase(label)}</option>)}
                  </select>
                </label>
                <button className="button button-secondary log-clear" onClick={downloadLog} disabled={!demoLog.length} aria-label="Export complete session log">
                  <Download size={14} /> Export
                </button>
                <button className="button button-secondary log-clear" onClick={() => setDemoLog([])} disabled={!demoLog.length} aria-label="Clear session log">
                  <Trash2 size={14} /> Clear
                </button>
              </div>
            </div>
            {demoLog.filter((entry) => entry.kind !== "frame").length ? (
              <ol className="session-log-list" aria-live="polite">
                {demoLog.filter((entry) => entry.kind !== "frame").slice(0, 8).map((entry) => (
                  <li key={entry.id} className={`session-log-entry log-${entry.kind}`}>
                    <time>{entry.time}</time>
                    <div><strong>{entry.title}</strong><p>{entry.detail}</p></div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="session-log-empty">Predictions and session updates will appear here.</p>
            )}
          </section>
        </div>
      </div>
      <div className="recognition-disclaimer">
        <ShieldCheck size={15} />
        <span>
          Assistive communication only. A model suggestion is not a diagnosis
          and cannot replace professional medical assessment.
        </span>
      </div>
    </section>
  );
}
export function Step({
  number,
  title,
  text,
  active,
}: {
  number: string;
  title: string;
  text: string;
  active: boolean;
}) {
  return (
    <div className={`step-row ${active ? "step-active" : ""}`}>
      <span className="step-number">
        {active ? <Check size={14} /> : number}
      </span>
      <span>
        <strong>{title}</strong>
        <small>{text}</small>
      </span>
    </div>
  );
}

export function Communications({
  history,
  onRemove,
  onUpdate,
  onClear,
}: {
  history: Communication[];
  onRemove: (id: string) => void;
  onUpdate: (id: string, note: string) => void;
  onClear: () => void;
}) {
  const [filter, setFilter] = useState("all"),
    [query, setQuery] = useState("");
  const filtered = useMemo(
    () =>
      history.filter(
        (item) =>
          (filter === "all" || item.label === filter) &&
          titleCase(item.label).toLowerCase().includes(query.toLowerCase()),
      ),
    [history, filter, query],
  );
  const labels = [...new Set(history.map((item) => item.label))];
  return (
    <>
      <PageHeading
        eyebrow="PATIENT COMMUNICATION"
        title="Confirmed messages"
        subtitle="A clear record of symptoms the patient chose to share."
        action={
          history.length > 0 && (
            <button className="button button-secondary" onClick={onClear}>
              <Trash2 size={16} /> Clear history
            </button>
          )
        }
      />
      <div className="history-note">
        <ShieldCheck size={17} />
        <span>
          <strong>Patient-confirmed only.</strong> Model suggestions are never
          added here automatically.
        </span>
        <span className="local-badge">Stored in this browser</span>
      </div>
      <section className="panel history-panel">
        <div className="history-toolbar">
          <div className="history-heading">
            <h3>
              Communication history <span>{history.length}</span>
            </h3>
            <p>
              {history.length === 1
                ? "1 confirmed message"
                : `${history.length} confirmed messages`}
            </p>
          </div>
          <div className="history-filters">
            <div className="search-field">
              <input
                aria-label="Search symptoms"
                placeholder="Search symptoms…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <select
              aria-label="Filter symptom"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="all">All symptoms</option>
              {labels.map((label) => (
                <option key={label} value={label}>
                  {titleCase(label)}
                </option>
              ))}
            </select>
          </div>
        </div>
        {filtered.length === 0 ? (
          <EmptyState
            icon={AudioLines}
            title={
              history.length ? "No matching messages" : "Nothing shared yet"
            }
            text={
              history.length
                ? "Adjust your search or filter."
                : "Once a patient confirms a sign, their message will be recorded here."
            }
            action={
              !history.length && (
                <Link
                  className="button button-primary button-small"
                  to="/recognize"
                >
                  <ScanFace size={15} /> Start recognition
                </Link>
              )
            }
          />
        ) : (
          <div className="history-list">
            {filtered.map((item) => (
              <div className="history-item" key={item.id}>
                <div className="history-date">
                  <span>
                    {new Intl.DateTimeFormat(undefined, { month: "short" })
                      .format(new Date(item.createdAt))
                      .toUpperCase()}
                  </span>
                  <strong>
                    {new Intl.DateTimeFormat(undefined, {
                      day: "2-digit",
                    }).format(new Date(item.createdAt))}
                  </strong>
                  <small>
                    {new Intl.DateTimeFormat(undefined, {
                      hour: "numeric",
                      minute: "2-digit",
                    }).format(new Date(item.createdAt))}
                  </small>
                </div>
                <div className="history-item-content">
                  <div className="history-item-title">
                    <span className="symptom-mark">
                      <HeartPulse size={17} />
                    </span>
                    <strong>Patient reports {article(item.label)}.</strong>
                    <span className="confirmed-tag">
                      <Check size={12} /> Confirmed
                    </span>
                  </div>
                  <div className="history-item-meta">
                    <span>
                      <Clock3 size={13} />
                      {formatDate(item.createdAt)}
                    </span>
                    <span className="model-confidence">
                      <Gauge size={13} />
                      Model confidence at confirmation:{" "}
                      {Math.round(item.confidence * 100)}%
                    </span>
                  </div>
                  <details className="note-editor">
                    <summary>
                      {item.note ? "Edit optional note" : "Add optional note"}
                    </summary>
                    <textarea
                      aria-label={`Optional note for ${titleCase(item.label)}`}
                      rows={2}
                      maxLength={500}
                      value={item.note}
                      onChange={(event) =>
                        onUpdate(item.id, event.target.value)
                      }
                      placeholder="Add context the patient wants to share…"
                    />
                  </details>
                </div>
                <button
                  className="icon-button delete-item"
                  aria-label="Delete confirmed communication"
                  onClick={() =>
                    window.confirm("Delete this confirmed communication?") &&
                    onRemove(item.id)
                  }
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
      <p className="privacy-footnote">
        <Info size={14} /> History is stored locally in this browser. No video
        or landmark sequence is retained.
      </p>
    </>
  );
}
export function Clinical({
  history,
  health,
}: {
  history: Communication[];
  health: Health | null;
}) {
  return (
    <>
      <PageHeading
        eyebrow="CLINICAL VIEW"
        title="Patient communication"
        subtitle="A concise view of symptoms the patient has confirmed."
        action={
          <span className="clinical-mode">
            <ShieldCheck size={14} /> Local demo view
          </span>
        }
      />
      <div className="clinical-banner">
        <div className="clinical-banner-icon">
          <FileText size={21} />
        </div>
        <div>
          <strong>Patient-led communication record</strong>
          <p>
            This view contains only patient-confirmed messages from this
            browser. It is not a clinical record or diagnosis.
          </p>
        </div>
      </div>
      <div className="clinical-summary-grid">
        <div className="clinical-summary">
          <span>CONFIRMED COMMUNICATIONS</span>
          <strong>{history.length}</strong>
          <small>In this local session</small>
        </div>
        <div className="clinical-summary">
          <span>SUPPORTED VOCABULARY</span>
          <strong>9</strong>
          <small>ASL symptom classes</small>
        </div>
        <div className="clinical-summary">
          <span>MODEL CHECKPOINT</span>
          <strong>{health?.model_available ? "Available" : "Missing"}</strong>
          <small>Results require patient confirmation</small>
        </div>
      </div>
      <section className="panel clinical-history">
        <div className="panel-heading">
          <div>
            <h3>Confirmed symptom messages</h3>
            <p>Newest communication first.</p>
          </div>
          <Link to="/communications" className="quiet-link">
            Manage history <ArrowRight size={14} />
          </Link>
        </div>
        {history.length ? (
          <div className="recent-list">
            {history.map((item) => (
              <div className="clinical-item" key={item.id}>
                <div className="clinical-item-mark">
                  <HeartPulse size={17} />
                </div>
                <div>
                  <strong>Patient reports {article(item.label)}.</strong>
                  <span>
                    <Clock3 size={13} />
                    {formatDate(item.createdAt)}
                  </span>
                  {item.note && <small>{item.note}</small>}
                </div>
                <div className="clinical-item-confidence">
                  <small>MODEL CONFIDENCE</small>
                  <strong>{Math.round(item.confidence * 100)}%</strong>
                </div>
                <span className="confirmed-tag">
                  <Check size={12} /> Confirmed
                </span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={FileText}
            title="No confirmed messages"
            text="Patient-confirmed communications will appear here."
            action={
              <Link
                to="/recognize"
                className="button button-secondary button-small"
              >
                <ScanFace size={15} /> Start recognition
              </Link>
            }
          />
        )}
      </section>
      <div className="clinical-note">
        <TriangleAlert size={16} />
        <span>
          Model confidence reflects the recogniser's output only. It is not a
          measure of symptom severity or clinical certainty.
        </span>
      </div>
    </>
  );
}
export function Dataset({ health }: { health: Health | null }) {
  const labels = health?.labels?.length ? health.labels : defaultLabels;
  return (
    <>
      <PageHeading
        eyebrow="MODEL & DATASET"
        title="What the model knows."
        subtitle="Transparent information about MediSign’s training data and recognition model."
      />
      <div className="data-status-banner">
        <div className="data-status-icon">
          <Activity size={20} />
        </div>
        <div>
          <strong>
            {health?.model_available
              ? "Local model checkpoint found"
              : "No trained checkpoint found"}
          </strong>
          <p>
            {health?.model_available
              ? "The local inference service can load a trained model."
              : "The original repository contains training code but no saved model weights."}
          </p>
        </div>
        <span
          className={`status-tag ${health?.model_available ? "status-good" : "status-missing"}`}
        >
          <span className="status-dot" />
          {health?.model_available ? "AVAILABLE" : "NOT TRAINED"}
        </span>
      </div>
      <div className="section-heading data-section-heading">
        <div>
          <h2>Dataset overview</h2>
          <p>Verified from the included landmark feature arrays.</p>
        </div>
        <span className="verified-label">
          <CheckCircle2 size={14} /> VERIFIED STRUCTURE
        </span>
      </div>
      <div className="data-stat-grid">
        <DataStat value="270" label="Sequences" detail="30 per symptom class" />
        <DataStat
          value="8,100"
          label="Frame files"
          detail="30 frames per sequence"
        />
        <DataStat
          value="1,662"
          label="Features / frame"
          detail="MediaPipe Holistic landmarks"
        />
        <DataStat
          value="9"
          label="Symptom classes"
          detail="American Sign Language"
        />
      </div>
      <section className="panel labels-panel">
        <div className="panel-heading">
          <div>
            <h3>Supported symptoms</h3>
            <p>Stable class order used by the original model.</p>
          </div>
          <span className="class-count">{labels.length} CLASSES</span>
        </div>
        <div className="label-grid">
          {labels.map((label, index) => (
            <div className="label-chip" key={label}>
              <span className="label-index">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span>{titleCase(label)}</span>
              <span className="sequence-count">30 sequences</span>
            </div>
          ))}
        </div>
      </section>
      <div className="model-details-grid">
        <section className="panel architecture-panel">
          <div className="panel-heading">
            <div>
              <h3>Verified model architecture</h3>
              <p>From the repository’s original Keras model.</p>
            </div>
            <div className="architecture-icon">
              <Activity size={18} />
            </div>
          </div>
          <div className="architecture-flow">
            <ArchLayer label="Input sequence" detail="30 × 1,662 features" />
            <ArchLayer label="LSTM · 64 units" detail="Return sequences" />
            <ArchLayer label="LSTM · 128 units" detail="Return sequences" />
            <ArchLayer label="LSTM · 64 units" detail="Sequence summary" />
            <ArchLayer label="Dense · 64 → 32" detail="ReLU activation" />
            <ArchLayer
              label="Softmax · 9 classes"
              detail="Sparse categorical cross entropy"
              last
            />
          </div>
          <p className="architecture-foot">
            <Info size={14} /> Adam optimizer. Feature input order: pose, face,
            left hand, right hand.
          </p>
        </section>
        <section className="panel evaluation-panel">
          <div className="panel-heading">
            <div>
              <h3>Training results</h3>
              <p>Metrics from local experiments only.</p>
            </div>
            <Gauge size={18} className="subtle-icon" />
          </div>
          {health?.model_available ? (
            <div className="evaluation-available">
              <CheckCircle2 size={19} />
              <strong>Checkpoint is available.</strong>
              <p>
                Training metric artifacts can be reviewed in{" "}
                <code>ml/results/</code> when generated by a local training run.
              </p>
              <span>Metrics are not inferred from checkpoint presence.</span>
            </div>
          ) : (
            <div className="no-metrics">
              <div className="no-metrics-icon">
                <FileText size={19} />
              </div>
              <strong>No experiment metrics recorded</strong>
              <p>
                The repository has no trained weights or evaluation report yet.
                Run the training script to generate actual held-out results.
              </p>
              <code>python -m ml.training.train</code>
            </div>
          )}
          <div className="evaluation-caveat">
            <TriangleAlert size={15} />
            <span>
              The dataset is small and has no signer identifiers. Evaluation is
              not signer-independent and does not establish clinical
              performance.
            </span>
          </div>
        </section>
      </div>
      <section className="panel limitations-panel">
        <div className="panel-heading">
          <div>
            <h3>Data and model limitations</h3>
            <p>Read these results in context.</p>
          </div>
          <BookOpen size={18} className="subtle-icon" />
        </div>
        <div className="limitation-grid">
          <Limitation
            title="Small dataset"
            text="Only 30 recorded sequences are available for each symptom sign."
          />
          <Limitation
            title="No signer metadata"
            text="The project cannot produce a signer-independent train and test split."
          />
          <Limitation
            title="ASL vocabulary"
            text="This model recognises nine collected signs, not unrestricted ASL conversation."
          />
          <Limitation
            title="Not clinically validated"
            text="Predictions do not indicate a diagnosis, severity, or medical probability."
          />
        </div>
      </section>
    </>
  );
}
function DataStat({
  value,
  label,
  detail,
}: {
  value: string;
  label: string;
  detail: string;
}) {
  return (
    <div className="data-stat">
      <strong>{value}</strong>
      <span>{label}</span>
      <small>{detail}</small>
    </div>
  );
}
function ArchLayer({
  label,
  detail,
  last = false,
}: {
  label: string;
  detail: string;
  last?: boolean;
}) {
  return (
    <div className={`arch-layer ${last ? "arch-last" : ""}`}>
      <span className="arch-node" />
      <div>
        <strong>{label}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}
function Limitation({ title, text }: { title: string; text: string }) {
  return (
    <div className="limitation">
      <span>
        <Info size={15} />
      </span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}
export function About() {
  return (
    <>
      <PageHeading
        eyebrow="ABOUT MEDISIGN"
        title="Communication comes first."
        subtitle="A local-first assistive communication project for patient-led ASL symptom sharing."
      />
      <div className="about-hero">
        <div className="about-hero-mark">
          <HeartPulse size={29} />
        </div>
        <div className="about-hero-copy">
          <span>THE PURPOSE</span>
          <h2>
            Make it easier to share a symptom, in the patient’s own language.
          </h2>
          <p>
            MediSign explores how computer vision and sequence recognition can
            support communication between deaf or hard-of-hearing people and
            healthcare professionals.
          </p>
        </div>
        <div className="about-decor">
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="about-grid">
        <section className="panel about-method">
          <div className="panel-heading">
            <div>
              <h3>How recognition works</h3>
              <p>A sequence-based ASL recognition workflow.</p>
            </div>
            <Activity size={18} className="subtle-icon" />
          </div>
          <div className="method-steps">
            <Method
              icon={Camera}
              number="01"
              title="Capture locally"
              text="The patient’s browser reads a live webcam stream. Video is not saved."
            />
            <Method
              icon={ScanFace}
              number="02"
              title="Extract landmarks"
              text="MediaPipe Holistic provides pose, face, and hand landmarks for each frame."
            />
            <Method
              icon={Activity}
              number="03"
              title="Recognise a sequence"
              text="A local LSTM model evaluates 30 frames for one of nine supported classes."
            />
            <Method
              icon={CheckCircle2}
              number="04"
              title="Confirm together"
              text="The patient can confirm, reject, or try the suggested symptom again."
            />
          </div>
        </section>
        <section className="panel about-boundaries">
          <div className="panel-heading">
            <div>
              <h3>Clear boundaries</h3>
              <p>Designed as a communication aid.</p>
            </div>
            <ShieldCheck size={18} className="subtle-icon" />
          </div>
          <div className="boundary-list">
            <Boundary
              icon={CheckCircle2}
              title="Patient remains in control"
              text="A prediction becomes a message only after the patient confirms it."
              good
            />
            <Boundary
              icon={CheckCircle2}
              title="No cloud service required"
              text="Inference runs through the local Python service."
              good
            />
            <Boundary
              icon={XCircle}
              title="Not a diagnostic system"
              text="MediSign does not identify or diagnose medical conditions."
            />
            <Boundary
              icon={XCircle}
              title="Not unrestricted translation"
              text="The model covers nine symptom signs, not general ASL."
            />
          </div>
        </section>
      </div>
      <section className="disclaimer-card">
        <div className="disclaimer-card-icon">
          <TriangleAlert size={20} />
        </div>
        <div>
          <span>IMPORTANT INFORMATION</span>
          <p>
            MediSign is an assistive communication tool. It is not a diagnostic
            system and does not replace professional medical assessment.
          </p>
        </div>
      </section>
      <div className="future-note">
        <span className="future-icon">
          <Plus size={18} />
        </span>
        <div>
          <strong>Designed to grow responsibly</strong>
          <p>
            Future language packs and vocabulary can be added without presenting
            this ASL model as an all-purpose sign language translator.
          </p>
        </div>
      </div>
    </>
  );
}
function Method({
  icon: Icon,
  number,
  title,
  text,
}: {
  icon: typeof Camera;
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="method-row">
      <span className="method-icon">
        <Icon size={17} />
      </span>
      <span className="method-number">{number}</span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}
function Boundary({
  icon: Icon,
  title,
  text,
  good = false,
}: {
  icon: typeof CheckCircle2;
  title: string;
  text: string;
  good?: boolean;
}) {
  return (
    <div className={`boundary-row ${good ? "boundary-good" : ""}`}>
      <Icon size={17} />
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}
