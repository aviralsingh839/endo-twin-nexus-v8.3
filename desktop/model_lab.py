"""V8.7 research Model Lab inspired by the CHRONO-PCOS V8.2 workflow.

This is an engineering/research surface:
UPLOAD -> INSPECT -> VALIDATE -> CONFIGURE -> TRAIN -> EVALUATE
-> COMPARE -> HUMAN REVIEW -> APPROVE -> DEPLOY.

The trained experiment is kept separate from the live CHRONO-PCOS research index.
Approval here does not make a model clinically validated and does not turn the
workstation into a diagnostic device.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import joblib

NOTICE = ("Research Model Lab only. Experimental models are not medical diagnoses. "
          "Synthetic or convenience data never establishes clinical validity.")

class ReviewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Human Review")
        self.setMinimumWidth(520)
        v=QVBoxLayout(self)
        v.addWidget(QLabel("Reviewer name / identifier"))
        self.reviewer=QLineEdit(); v.addWidget(self.reviewer)
        v.addWidget(QLabel("Review note"))
        self.note=QTextEdit(); self.note.setPlaceholderText("Document the research decision and limitations."); v.addWidget(self.note)
        b=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); v.addWidget(b)
    def values(self):
        return self.reviewer.text().strip(), self.note.toPlainText().strip()

class ModelLabWidget(QWidget):
    def __init__(self, root: Path, parent=None):
        super().__init__(parent)
        self.root=Path(root); self.store=self.root/"data"/"model_lab"; self.store.mkdir(parents=True,exist_ok=True)
        self.runs=self.store/"runs"; self.runs.mkdir(parents=True,exist_ok=True)
        self.df: Optional[pd.DataFrame]=None; self.file_path: Optional[Path]=None
        self.target_col=""; self.model_path=None; self.metrics={}
        self.reviewed=False; self.approved=False
        self._build()

    def _card(self,title,value,detail=""):
        f=QFrame(); f.setObjectName("card"); v=QVBoxLayout(f)
        a=QLabel(title); a.setObjectName("eyebrow"); v.addWidget(a)
        b=QLabel(str(value)); b.setObjectName("value"); v.addWidget(b)
        c=QLabel(detail); c.setObjectName("muted"); c.setWordWrap(True); v.addWidget(c)
        return f,b

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(18,16,18,16)
        t=QLabel("Research Model Lab"); t.setObjectName("title"); outer.addWidget(t)
        n=QLabel(NOTICE); n.setObjectName("warning"); n.setWordWrap(True); outer.addWidget(n)
        self.tabs=QTabWidget(); outer.addWidget(self.tabs,1)
        self.tabs.addTab(self._overview(), "Overview")
        self.tabs.addTab(self._dataset_page(), "Dataset")
        self.tabs.addTab(self._train_page(), "Training")
        self.tabs.addTab(self._eval_page(), "Evaluation")
        self.tabs.addTab(self._registry_page(), "Registry")

    def _overview(self):
        p=QWidget(); v=QVBoxLayout(p)
        g=QGridLayout()
        self.c_dataset,self.v_dataset=self._card("Dataset","NONE","No dataset loaded")
        self.c_rows,self.v_rows=self._card("Rows","0","Current tabular rows")
        self.c_features,self.v_features=self._card("Features","0","Usable model columns")
        self.c_auc,self.v_auc=self._card("ROC AUC","NOT EVALUATED","Holdout only")
        self.c_status,self.v_status=self._card("Model status","EXPERIMENT","Explicit human gate")
        self.c_active,self.v_active=self._card("Active experiment","NONE","Research-only")
        for i,b in enumerate([self.c_dataset,self.c_rows,self.c_features,self.c_auc,self.c_status,self.c_active]):g.addWidget(b,0,i)
        v.addLayout(g)
        flow=QFrame(); flow.setObjectName("hero"); fv=QVBoxLayout(flow)
        fv.addWidget(QLabel("CONTROLLED WORKFLOW"))
        self.flow_label=QLabel("UPLOAD → INSPECT → VALIDATE → CONFIGURE → TRAIN → EVALUATE → COMPARE → HUMAN REVIEW → APPROVE → DEPLOY")
        self.flow_label.setWordWrap(True); self.flow_label.setStyleSheet("font-weight:900;font-size:13px;"); fv.addWidget(self.flow_label)
        self.overview_log=QTextEdit(); self.overview_log.setReadOnly(True); self.overview_log.setMaximumHeight(190); fv.addWidget(self.overview_log)
        v.addWidget(flow); v.addStretch()
        return p

    def _dataset_page(self):
        p=QWidget(); v=QVBoxLayout(p)
        row=QHBoxLayout(); self.path_label=QLabel("No file"); self.path_label.setObjectName("muted"); row.addWidget(self.path_label,1)
        up=QPushButton("Upload CSV / XLSX"); up.setObjectName("primary"); up.clicked.connect(self._upload); row.addWidget(up)
        v.addLayout(row)
        form=QHBoxLayout(); self.target=QComboBox(); self.target.currentTextChanged.connect(self._target_changed); form.addWidget(QLabel("Target:")); form.addWidget(self.target,1)
        self.group=QComboBox(); form.addWidget(QLabel("Group ID:")); form.addWidget(self.group,1); v.addLayout(form)
        self.dataset_report=QTextEdit(); self.dataset_report.setReadOnly(True); v.addWidget(self.dataset_report,1)
        self.table=QTableWidget(0,0); self.table.setMaximumHeight(250); v.addWidget(self.table)
        return p

    def _train_page(self):
        p=QWidget(); v=QVBoxLayout(p)
        info=QLabel("Prototype trainer: numeric + categorical tabular features, imputation, scaling/encoding and balanced logistic regression. Patient/group IDs are excluded from model features.")
        info.setObjectName("muted"); info.setWordWrap(True); v.addWidget(info)
        row=QHBoxLayout(); self.test_pct=QSpinBox(); self.test_pct.setRange(10,40); self.test_pct.setValue(30)
        row.addWidget(QLabel("Holdout %")); row.addWidget(self.test_pct); row.addStretch()
        b=QPushButton("Validate dataset"); b.setObjectName("secondary"); b.clicked.connect(self._validate); row.addWidget(b)
        self.train_btn=QPushButton("TRAIN EXPERIMENT"); self.train_btn.setObjectName("primary"); self.train_btn.clicked.connect(self._train); row.addWidget(self.train_btn)
        v.addLayout(row); self.train_log=QTextEdit(); self.train_log.setReadOnly(True); v.addWidget(self.train_log,1)
        return p

    def _eval_page(self):
        p=QWidget(); v=QVBoxLayout(p)
        self.eval_text=QTextEdit(); self.eval_text.setReadOnly(True); self.eval_text.setPlaceholderText("Evaluation appears after training."); v.addWidget(self.eval_text)
        row=QHBoxLayout()
        compare=QPushButton("COMPARE WITH PREVIOUS RUNS"); compare.setObjectName("secondary"); compare.clicked.connect(self._compare); row.addWidget(compare)
        review=QPushButton("HUMAN REVIEW"); review.setObjectName("secondary"); review.clicked.connect(self._review); row.addWidget(review)
        row.addStretch(); v.addLayout(row)
        return p

    def _registry_page(self):
        p=QWidget(); v=QVBoxLayout(p)
        self.registry_list=QListWidget(); v.addWidget(self.registry_list,1)
        row=QHBoxLayout()
        self.approve_btn=QPushButton("APPROVE"); self.approve_btn.setObjectName("primary"); self.approve_btn.clicked.connect(self._approve); row.addWidget(self.approve_btn)
        dep=QPushButton("DEPLOY EXPERIMENT"); dep.setObjectName("secondary"); dep.clicked.connect(self._deploy); row.addWidget(dep)
        exp=QPushButton("EXPORT EXPERIMENT JSON"); exp.setObjectName("secondary"); exp.clicked.connect(self._export); row.addWidget(exp)
        v.addLayout(row)
        self.registry_status=QLabel("Nothing registered."); self.registry_status.setObjectName("muted"); self.registry_status.setWordWrap(True); v.addWidget(self.registry_status)
        return p

    def _log(self,msg):
        stamp=time.strftime("%H:%M:%S")
        self.overview_log.append(f"{stamp} • {msg}")
        if hasattr(self,"train_log"): self.train_log.append(f"{stamp} • {msg}")

    def _upload(self):
        p,_=QFileDialog.getOpenFileName(self,"Select research dataset","","Tabular data (*.csv *.xlsx)")
        if not p:return
        try:
            fp=Path(p); df=pd.read_csv(fp) if fp.suffix.lower()==".csv" else pd.read_excel(fp)
        except Exception as e:
            self.dataset_report.setPlainText(f"Import failed: {type(e).__name__}: {e}"); return
        self.df=df.copy(); self.file_path=fp; self.reviewed=False; self.approved=False
        self.target.clear(); self.target.addItems([str(c) for c in df.columns])
        self.group.clear(); self.group.addItem("None")
        self.group.addItems([str(c) for c in df.columns if str(c).lower() in {"patient_id","subject_id","participant_id","group_id"}])
        self.path_label.setText(str(fp)); self.v_dataset.setText(fp.name); self.v_rows.setText(str(len(df))); self.v_features.setText(str(max(0,len(df.columns)-1)))
        self._inspect(); self._log(f"Uploaded {fp.name}: {len(df)} rows, {len(df.columns)} columns.")

    def _target_changed(self,text):
        self.target_col=text
        if self.df is not None:self._inspect()

    def _inspect(self):
        if self.df is None:return
        df=self.df; miss=df.isna().sum(); lines=[f"FILE: {self.file_path}",f"ROWS: {len(df)}",f"COLUMNS: {len(df.columns)}","",f"TARGET: {self.target_col or 'NOT SELECTED'}","TARGET COUNTS:"]
        if self.target_col and self.target_col in df:
            lines += [f"  {k}: {v}" for k,v in df[self.target_col].value_counts(dropna=False).to_dict().items()]
        lines += ["","MISSING VALUES:"]+[f"  {k}: {int(v)}" for k,v in miss.items() if int(v)>0][:40]
        self.dataset_report.setPlainText("\n".join(lines))
        self.table.setColumnCount(min(len(df.columns),12)); self.table.setRowCount(min(len(df),8)); self.table.setHorizontalHeaderLabels([str(x) for x in df.columns[:12]])
        for r in range(min(len(df),8)):
            for c in range(min(len(df.columns),12)): self.table.setItem(r,c,QTableWidgetItem(str(df.iat[r,c])))

    def _validate(self):
        if self.df is None:return False,"No dataset loaded."
        if not self.target_col:return False,"Select a target column."
        y=self.df[self.target_col]
        if y.dropna().nunique()!=2:return False,"Target must have exactly two non-null classes for this prototype."
        numeric=[c for c in self.df.columns if c!=self.target_col and c not in {self.group.currentText()}]
        if not numeric:return False,"No feature columns remain."
        return True,f"Validation OK: binary target, {len(numeric)} candidate feature columns."
    
    def _train(self):
        ok,msg=self._validate()
        if not ok:self.train_log.setPlainText("TRAIN BLOCKED: "+msg); return
        df=self.df.dropna(subset=[self.target_col]).copy()
        y_raw=df[self.target_col]
        classes=list(pd.unique(y_raw))
        mapping={classes[0]:0,classes[1]:1}; y=y_raw.map(mapping).to_numpy()
        group_col=self.group.currentText() if self.group.currentText()!="None" else None
        drop={self.target_col} | ({group_col} if group_col else set())
        X=df.drop(columns=list(drop),errors="ignore")
        usable=[c for c in X.columns if X[c].dtype.kind in "biufcOUS" and X[c].nunique(dropna=True)>1]
        X=X[usable]
        cat=[c for c in X.columns if X[c].dtype.kind not in "biufc"]
        num=[c for c in X.columns if c not in cat]
        pre=ColumnTransformer([
            ("num",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),num),
            ("cat",Pipeline([("impute",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))]),cat),
        ],remainder="drop")
        model=Pipeline([("pre",pre),("clf",LogisticRegression(max_iter=1500,class_weight="balanced",random_state=42))])
        try:
            if group_col:
                groups=df[group_col].astype(str).to_numpy()
                splitter=GroupShuffleSplit(n_splits=1,test_size=self.test_pct.value()/100.0,random_state=42)
                train_idx,test_idx=next(splitter.split(X,y,groups))
            else:
                train_idx,test_idx=train_test_split(np.arange(len(y)),test_size=self.test_pct.value()/100.0,random_state=42,stratify=y)
            model.fit(X.iloc[train_idx],y[train_idx])
            p=model.predict_proba(X.iloc[test_idx])[:,1]
            pred=(p>=0.5).astype(int)
        except Exception as e:
            self.train_log.setPlainText(f"TRAIN FAILED: {type(e).__name__}: {e}"); return
        self.metrics={
            "status":"EVALUATED","n_train":int(len(train_idx)),"n_test":int(len(test_idx)),
            "accuracy":float(accuracy_score(y[test_idx],pred)),
            "balanced_accuracy":float(balanced_accuracy_score(y[test_idx],pred)),
            "roc_auc":float(roc_auc_score(y[test_idx],p)),
            "classes":[str(c) for c in classes],"features":list(X.columns),
            "group_split":bool(group_col),"target":self.target_col,"source_file":str(self.file_path),
            "trained_at":time.time(),"research_only":True,
        }
        stamp=time.strftime("%Y%m%d_%H%M%S"); run=self.runs/f"run_{stamp}"; run.mkdir(exist_ok=True)
        self.model_path=run/"model.joblib"; joblib.dump({"model":model,"classes":classes,"metrics":self.metrics},self.model_path)
        (run/"metrics.json").write_text(json.dumps(self.metrics,indent=2),encoding="utf-8")
        self.v_auc.setText(f"{self.metrics['roc_auc']:.3f}"); self.v_status.setText("CANDIDATE"); self.registry_list.addItem(f"CHRONO-EXP-{stamp} • CANDIDATE • AUC {self.metrics['roc_auc']:.3f}")
        self.eval_text.setPlainText(json.dumps(self.metrics,indent=2))
        self.train_log.setPlainText(f"TRAIN COMPLETE\n{json.dumps(self.metrics,indent=2)}\n\nThis metric is an internal research experiment, not a clinical performance claim.")
        self._log("Training/evaluation completed; candidate remains unapproved.")

    def _compare(self):
        previous=[]
        for p in sorted(self.runs.glob("run_*/metrics.json")):
            try:m=json.loads(p.read_text(encoding="utf-8")); previous.append((p.parent.name,m.get("roc_auc")))
            except Exception:pass
        if not previous:self.eval_text.append("\nNo previous runs found.")
        else:self.eval_text.append("\nPREVIOUS RUNS:\n"+"\n".join(f"{n}: ROC AUC {a:.3f}" if a is not None else f"{n}: NOT EVALUATED" for n,a in previous))

    def _review(self):
        if self.metrics.get("status")!="EVALUATED": self.eval_text.append("HUMAN REVIEW BLOCKED: no evaluated experiment."); return
        d=ReviewDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        reviewer,note=d.values()
        if not reviewer:self.eval_text.append("HUMAN REVIEW BLOCKED: reviewer required."); return
        self.reviewed=True; self.registry_status.setText(f"Reviewed by {reviewer}. Note: {note or 'none'}"); self._log(f"Human review recorded for current candidate by {reviewer}.")
    
    def _approve(self):
        if not self.reviewed:self.registry_status.setText("APPROVAL BLOCKED: complete HUMAN REVIEW first."); return
        if self.metrics.get("status")!="EVALUATED":self.registry_status.setText("APPROVAL BLOCKED: experiment has no evaluation."); return
        self.approved=True; self.v_status.setText("APPROVED"); self.registry_status.setText("APPROVED for research deployment only after explicit human review. Not clinically validated."); self._log("Human approval recorded.")

    def _deploy(self):
        if not self.approved:self.registry_status.setText("DEPLOY BLOCKED: explicit APPROVE is required."); return
        state={"approved":True,"model_path":str(self.model_path),"metrics":self.metrics,"deployed_at":time.time(),"clinical_validation":"NOT ESTABLISHED"}
        (self.store/"active_experiment.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
        self.v_active.setText(Path(self.model_path).parent.name if self.model_path else "NONE")
        self._log("Research experiment pointer updated. Live CHRONO-PCOS index is unchanged.")

    def _export(self):
        p,_=QFileDialog.getSaveFileName(self,"Export experiment JSON",str(self.store/"experiment.json"),"JSON (*.json)")
        if not p:return
        payload={"metrics":self.metrics,"model_path":str(self.model_path) if self.model_path else None,"reviewed":self.reviewed,"approved":self.approved}
        Path(p).write_text(json.dumps(payload,indent=2),encoding="utf-8")
        self.registry_status.setText(f"Exported {p}")
