import { Document, Page, View, Text, Image, StyleSheet } from "@react-pdf/renderer";
import { getReportTypeConfig } from "../lib/reportTypes";
import { CATEGORY_ORDER } from "../lib/categories";

const PAGE_MARGIN_X = 28;
const PAGE_MARGIN_TOP = 18;
const PAGE_MARGIN_BOTTOM = 32;
const HEADER_HEIGHT = 92;
const HEADER_GAP = 14;

const styles = StyleSheet.create({
  page: {
    paddingTop: PAGE_MARGIN_TOP + HEADER_HEIGHT + HEADER_GAP,
    paddingHorizontal: PAGE_MARGIN_X,
    paddingBottom: PAGE_MARGIN_BOTTOM,
    fontFamily: "Helvetica",
    fontSize: 10,
    color: "#111827",
  },
  header: {
    position: "absolute",
    top: PAGE_MARGIN_TOP,
    left: PAGE_MARGIN_X,
    right: PAGE_MARGIN_X,
    height: HEADER_HEIGHT,
    flexDirection: "row",
  },
  col: {
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: "#9ca3af",
    height: HEADER_HEIGHT,
    justifyContent: "center",
  },
  colLogo: {
    width: "22%",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 6,
    marginRight: 8,
  },
  colTitle: {
    width: "48%",
    alignItems: "stretch",
  },
  colMeta: {
    width: "30%",
    alignItems: "stretch",
    justifyContent: "flex-start",
    paddingHorizontal: 0,
    paddingVertical: 0,
    marginLeft: 8,
  },
  metaCell: {
    flexGrow: 1,
    flexShrink: 1,
    flexBasis: 0,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 6,
  },
  metaDivider: {
    height: 1,
    backgroundColor: "#6b7280",
    width: "100%",
  },
  logo: {
    width: 90,
    height: 52,
  },
  titleMain: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  title: {
    fontSize: 13,
    fontFamily: "Helvetica-Bold",
    color: "#374151",
    textAlign: "center",
    lineHeight: 1.2,
  },
  moduloWrap: {
    borderTopWidth: 1.5,
    borderTopColor: "#4b5563",
    borderStyle: "solid",
    paddingVertical: 4,
  },
  modulo: {
    textAlign: "center",
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    letterSpacing: 1.4,
    color: "#374151",
  },
  formCode: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: "#374151",
    textAlign: "center",
  },
  meta: {
    fontSize: 8,
    color: "#374151",
    textAlign: "center",
  },
  infoRow: {
    flexDirection: "row",
    marginBottom: 12,
  },
  infoCol: {
    width: "50%",
    paddingRight: 10,
  },
  label: {
    fontSize: 8,
    letterSpacing: 0.8,
    color: "#64748b",
    textTransform: "uppercase",
    marginBottom: 3,
  },
  value: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: "#0f172a",
  },
  sub: {
    fontSize: 9,
    color: "#475569",
    marginTop: 2,
  },
  sissBox: {
    borderWidth: 1.5,
    borderColor: "#7dd3fc",
    backgroundColor: "#f0f9ff",
    padding: 8,
    marginBottom: 10,
  },
  sissTitle: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: "#0c4a6e",
    marginBottom: 6,
  },
  tableRow: {
    flexDirection: "row",
    borderBottomWidth: 0.5,
    borderColor: "#bae6fd",
    paddingVertical: 3,
  },
  th: {
    fontSize: 7,
    letterSpacing: 0.6,
    color: "#0369a1",
    textTransform: "uppercase",
  },
  cellCode: { width: "28%", fontFamily: "Courier", fontSize: 9, color: "#0c4a6e" },
  cellDesc: { width: "52%", fontSize: 9, color: "#334155" },
  cellQty: { width: "20%", textAlign: "right", fontFamily: "Helvetica-Bold" },
  ricette: { marginBottom: 10 },
  ricetteTitle: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    marginBottom: 4,
    color: "#0f172a",
  },
  ricetta: { fontSize: 9, marginBottom: 2, color: "#334155" },
  sectionTitle: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    marginBottom: 6,
  },
  groupTitle: {
    fontSize: 8,
    letterSpacing: 0.7,
    color: "#64748b",
    textTransform: "uppercase",
    marginTop: 6,
    marginBottom: 3,
  },
  examRow: {
    flexDirection: "row",
    marginBottom: 2,
  },
  examCode: {
    width: 78,
    fontFamily: "Courier",
    fontSize: 8,
    color: "#64748b",
  },
  examName: {
    flex: 1,
    fontSize: 9,
    color: "#1e293b",
  },
  notes: { marginTop: 10 },
  notesText: { fontSize: 9, color: "#334155" },
  sign: {
    marginTop: 28,
    alignItems: "flex-end",
  },
  signLine: {
    fontSize: 9,
    color: "#475569",
    borderTopWidth: 0.6,
    borderColor: "#94a3b8",
    paddingTop: 4,
    width: 180,
    textAlign: "center",
  },
});

function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function PdfHeader({ cfg, logoSrc }) {
  return (
    <View style={styles.header} fixed>
      <View style={[styles.col, styles.colLogo]}>
        {logoSrc ? <Image src={logoSrc} style={styles.logo} /> : null}
      </View>
      <View style={[styles.col, styles.colTitle]}>
        <View style={styles.titleMain}>
          {(cfg.titleLines || []).map((line) => (
            <Text key={line} style={styles.title}>{line}</Text>
          ))}
          <Text style={styles.title}>{cfg.subtitle}</Text>
        </View>
        <View style={styles.moduloWrap}>
          <Text style={styles.modulo}>{cfg.modulo}</Text>
        </View>
      </View>
      <View style={[styles.col, styles.colMeta]}>
        <View style={styles.metaCell}>
          <Text style={styles.formCode}>{cfg.formCode}</Text>
        </View>
        <View style={styles.metaDivider} />
        <View style={styles.metaCell}>
          <Text
            style={styles.meta}
            render={({ pageNumber, totalPages }) => `PAGINA: ${pageNumber} DI ${totalPages}`}
          />
        </View>
        <View style={styles.metaDivider} />
        <View style={styles.metaCell}>
          <Text style={styles.meta}>REVISIONE: {cfg.revision}</Text>
        </View>
        <View style={styles.metaDivider} />
        <View style={styles.metaCell}>
          <Text style={styles.meta}>DATA: {cfg.date}</Text>
        </View>
      </View>
    </View>
  );
}

export default function ReportPdfDocument({
  reportType = "ige",
  selectedItems = [],
  patient = {},
  doctorName = "",
  notes = "",
  letterhead = "",
  aggregation,
  ricette = [],
  logoSrc,
}) {
  const cfg = getReportTypeConfig(reportType);
  const codeField = cfg.codeField;
  const grouped = cfg.groupByCategory
    ? CATEGORY_ORDER.map((type) => ({
        type,
        items: selectedItems.filter((a) => a.type === type),
      })).filter((g) => g.items.length)
    : [{ type: null, items: selectedItems }];

  return (
    <Document>
      <Page size="A4" style={styles.page} wrap>
        <PdfHeader cfg={cfg} logoSrc={logoSrc} />

        {letterhead ? (
          <Text style={{ fontSize: 8, color: "#64748b", marginBottom: 8 }}>{letterhead}</Text>
        ) : null}

        <View style={styles.infoRow}>
          <View style={styles.infoCol}>
            <Text style={styles.label}>Paziente</Text>
            <Text style={styles.value}>{patient.first_name || ""} {patient.last_name || ""}</Text>
            <Text style={styles.sub}>Nato/a il {fmtDate(patient.dob)}</Text>
          </View>
          <View style={styles.infoCol}>
            <Text style={styles.label}>Medico richiedente</Text>
            <Text style={styles.value}>{doctorName || "—"}</Text>
          </View>
        </View>

        {aggregation?.codes?.length > 0 ? (
          <View style={styles.sissBox}>
            <Text style={styles.sissTitle}>Codici SISS da riportare sulla ricetta</Text>
            <View style={styles.tableRow}>
              <Text style={[styles.cellCode, styles.th]}>Codice SISS</Text>
              <Text style={[styles.cellDesc, styles.th]}>Descrizione</Text>
              <Text style={[styles.cellQty, styles.th]}>Quantità</Text>
            </View>
            {aggregation.codes.map((c) => (
              <View key={c.siss_code} style={styles.tableRow}>
                <Text style={styles.cellCode}>{c.siss_code}</Text>
                <Text style={styles.cellDesc}>{c.description}</Text>
                <Text style={styles.cellQty}>× {c.quantity}</Text>
              </View>
            ))}
          </View>
        ) : null}

        {ricette.length > 0 ? (
          <View style={styles.ricette}>
            <Text style={styles.ricetteTitle}>Distribuzione su ricette (max 8 prestazioni per ricetta)</Text>
            {ricette.map((r, i) => (
              <Text key={i} style={styles.ricetta}>
                Ricetta {i + 1}: {r.map((it) => `${it.siss_code} × ${it.quantity}`).join("  ·  ")}
              </Text>
            ))}
          </View>
        ) : null}

        <Text style={styles.sectionTitle}>Esami richiesti ({selectedItems.length})</Text>
        {grouped.map((g) => (
          <View key={g.type || "list"}>
            {g.type ? (
              <Text style={styles.groupTitle}>{g.type} · {g.items.length}</Text>
            ) : null}
            {g.items.map((a) => (
              <View key={a[codeField]} style={styles.examRow} wrap={false}>
                <Text style={styles.examCode}>{a[codeField]}</Text>
                <Text style={styles.examName}>{a.name}</Text>
              </View>
            ))}
          </View>
        ))}

        <View style={styles.notes}>
          <Text style={styles.label}>Note</Text>
          <Text style={styles.notesText}>{notes || "—"}</Text>
        </View>

        <View style={styles.sign}>
          <Text style={styles.signLine}>Firma del medico</Text>
        </View>
      </Page>
    </Document>
  );
}
