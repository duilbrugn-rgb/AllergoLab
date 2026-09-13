import React, { act } from "react";
import { createRoot } from "react-dom/client";

jest.mock("../lib/api", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));
jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { role: "user" }, logout: jest.fn() }),
}));
jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));

const hiddenComponents = [
  "Header", "PatientForm", "IggSissSummary", "ReportModal",
  "AdminAllergens", "AdminUsers", "AuditLog",
  "AdminProfiles", "ProfileSelector",
];
hiddenComponents.forEach((name) => {
  jest.doMock(`../components/${name}`, () => ({
    __esModule: true,
    default: () => null,
  }));
});

jest.doMock("../components/DualList", () => ({
  __esModule: true,
  default: ({ setSelectedCodes }) => (
    <button data-testid="select-exam"
      onClick={() => setSelectedCodes(["f1"])}>
      Seleziona esame
    </button>
  ),
}));
jest.doMock("../components/SissSummary", () => ({
  __esModule: true,
  default: ({ aggregation }) => (
    <output data-testid="aggregation">
      {JSON.stringify(aggregation)}
    </output>
  ),
}));
jest.doMock("../components/ui/button", () => ({
  Button: ({ children, onClick, disabled, ...props }) => (
    <button onClick={onClick} disabled={disabled}
      data-testid={props["data-testid"]}>
      {children}
    </button>
  ),
}));
jest.doMock("../components/ui/card", () => ({
  Card: ({ children }) => <div>{children}</div>,
}));
jest.doMock("../components/ui/tabs", () => {
  const Wrapper = ({ children }) => <div>{children}</div>;
  return {
    Tabs: Wrapper, TabsList: Wrapper,
    TabsTrigger: Wrapper, TabsContent: Wrapper,
  };
});

const AppPage = require("./AppPage").default;
const api = require("../lib/api").default;

test("una risposta arrivata dopo Nuova prescrizione non ripristina i risultati", async () => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  jest.useFakeTimers();
  api.get.mockResolvedValue({ data: [] });
  let finishRequest;
  api.post.mockImplementation(() => new Promise((resolve) => {
    finishRequest = resolve;
  }));

  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);

  try {
    await act(async () => { root.render(<AppPage />); });

    await act(async () => {
      container.querySelector('[data-testid="select-exam"]').click();
    });
    await act(async () => { jest.advanceTimersByTime(250); });

    expect(api.post).toHaveBeenCalledWith("/aggregate", { codes: ["f1"] });
    expect(typeof finishRequest).toBe("function");

    await act(async () => {
      container.querySelector('[data-testid="btn-new-prescription"]').click();
    });

    const readAggregation = () => JSON.parse(
      container.querySelector('[data-testid="aggregation"]').textContent
    );
    expect(readAggregation().total).toBe(0);

    await act(async () => {
      finishRequest({
        data: {
          total: 1,
          codes: [{ siss_code: "0090681.00", quantity: 1 }],
        },
      });
    });

    expect(readAggregation().total).toBe(0);
    expect(readAggregation().codes).toEqual([]);
    expect(container.querySelector(
      '[data-testid="btn-preview-report-button"]'
    ).disabled).toBe(true);
  } finally {
    await act(async () => { root.unmount(); });
    container.remove();
    jest.useRealTimers();
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
  }
});
