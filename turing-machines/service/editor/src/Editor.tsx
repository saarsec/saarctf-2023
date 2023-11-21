import React, {Component} from "react";

interface StateAction {
    c: string;
    a: string[];
    h: number;
    s: string;
}

interface State {
    name: string;
    actions: StateAction[];
}

type ActionEditorProps = {
    action: StateAction;
    ident: string;
    onChangeAttr: (field: string, value: any) => void;
    onRemoveAction: () => void;
}

type ActionEditorState = {
    action: StateAction;
    h: string;
    actionText: string;
}

export class ActionEditor extends Component<ActionEditorProps, ActionEditorState> {
    public key: string;

    constructor(props: ActionEditorProps) {
        super(props);
        this.state = {
            action: props.action,
            h: '' + props.action.h,
            actionText: this.props.action.a.join('\n')
        };
        this.key = props.ident;
    }

    componentDidUpdate(prevProps: ActionEditorProps, prevState: ActionEditorState) {
        if (prevProps.action !== this.props.action) {
            this.setState({
                action: this.props.action,
                h: '' + this.props.action.h,
                actionText: prevProps.action.a.join('\n') === this.props.action.a.join('\n') ? this.state.actionText : this.props.action.a.join('\n')
            });
        }
    }

    render() {
        return <div className="row">
            <div className="col-md-3">
                <div className="form-floating mb-1">
                    <input type="text" className="form-control" id={this.key + '_c'} placeholder=""
                           value={this.state.action.c} onChange={e => this.updateC(e.target.value)}/>
                    <label htmlFor={this.key + '_c'}>Condition</label>
                </div>
            </div>
            <div className="col-md-3">
                <div className="form-floating mb-1">
                <textarea className="form-control" id="stateName" placeholder=""
                          value={this.state.actionText} onChange={e => this.updateA(e.target.value)}/>
                    <label htmlFor="stateName">Actions (one per line)</label>
                </div>
            </div>
            <div className="col-md-3">
                <div className="form-floating mb-1">
                    <input type="text" className="form-control" id={this.key + '_s'} placeholder=""
                           value={this.state.action.s} onChange={e => this.updateS(e.target.value)}/>
                    <label htmlFor={this.key + '_s'}>Next State</label>
                </div>
            </div>
            <div className="col-md-3 d-flex flex-row align-items-center">
                <div className="form-floating mb-1">
                    <input type="number" className="form-control" id={this.key + '_h'} placeholder=""
                           value={this.state.h} onChange={e => this.updateH(e.target.value)}/>
                    <label htmlFor={this.key + '_h'}>Head Movement</label>
                </div>

                <div className="mx-1">
                    <button type="button" className="btn btn-outline-danger btn-sm" title="Remove Action"
                            onClick={this.props.onRemoveAction}
                    >x
                    </button>
                </div>
            </div>
        </div>
    }

    updateC(c: string) {
        this.setState({action: {...this.state.action, c: c}, h: this.state.h, actionText: this.state.actionText});
        this.props.onChangeAttr('c', c);
    }

    updateH(h: string) {
        let parsedH = parseInt(h);
        if (isNaN(parsedH)) parsedH = this.state.action.h;
        this.setState({action: {...this.state.action, h: parsedH}, h: h, actionText: this.state.actionText});
        this.props.onChangeAttr('h', parsedH);
    }

    updateS(s: string) {
        this.setState({action: {...this.state.action, s: s}, h: this.state.h, actionText: this.state.actionText});
        this.props.onChangeAttr('s', s);
    }

    updateA(a: string) {
        let lst = a.split('\n');
        this.setState({action: {...this.state.action, a: lst}, h: this.state.h, actionText: a});
        this.props.onChangeAttr('a', lst.map(line => line.trim()).filter(line => line.length > 0));
    }
}


type StateEditorProps = {
    state: State;
    ident: string;
    onChangeName: (name: string) => void;
    onChangeActions: (actions: StateAction[]) => void;
    onRemoveState: () => void;
}

export class StateEditor extends Component<StateEditorProps, State> {
    public key: string;

    constructor(props: StateEditorProps) {
        super(props);
        this.state = props.state;
        this.key = props.ident;
    }

    componentDidUpdate(prevProps: StateEditorProps, prevState: State) {
        if (prevProps.state !== this.props.state) {
            this.setState(this.props.state);
        }
    }

    render() {
        let actions = this.state.actions.map(
            (action, index) => <ActionEditor action={action} ident={this.key + '_' + index}
                                             onChangeAttr={this.updateAction.bind(this, index)}
                                             onRemoveAction={this.removeAction.bind(this, index)}/>
        );
        return <div className="card mb-3">
            <div className="card-body">
                <div className="form-floating mb-1">
                    <input type="text" className="form-control" id={this.key + "_name"} placeholder=""
                           value={this.state.name}
                           onChange={e => this.updateName(e.target.value)}
                    />
                    <label htmlFor={this.key + "_name"}>State Name</label>
                </div>
                {actions}
                <div className="d-flex flex-row justify-content-between">
                    <button type="button" className="btn btn-primary btn-sm" onClick={this.addAction}>
                        + add action
                    </button>
                    <button type="button" className="btn btn-outline-danger btn-sm" onClick={this.props.onRemoveState}>
                        x remove this state
                    </button>
                </div>
            </div>
        </div>
    }

    addAction = () => {
        let newActions = [...this.state.actions, {c: "", a: [], h: 0, s: ""}]
        this.setState({
            name: this.state.name,
            actions: newActions
        });
        this.props.onChangeActions(newActions);
    }

    updateName = (name: string) => {
        this.setState({
            name: name,
            actions: this.state.actions
        });
        this.props.onChangeName(name);
    }

    updateAction(index: number, field: string, value: any) {
        let newValues: any = {};
        newValues[field] = value;
        let newAction = {...this.state.actions[index], ...newValues};
        let newActions = this.state.actions.map((action, i) => i === index ? newAction : action);
        this.setState({
            name: this.state.name,
            actions: newActions
        });
        this.props.onChangeActions(newActions);
    }

    removeAction(index: number) {
        let newActions = this.state.actions.filter((_, i) => i !== index);
        this.setState({
            name: this.state.name,
            actions: newActions
        });
        this.props.onChangeActions(newActions);
    }
}

type EditorProps = {
    machine?: State[];
    name: string;
}

type EditorComponentState = {
    machine: State[];
};

export default class Editor extends Component<EditorProps, EditorComponentState> {
    constructor(props: EditorProps) {
        super(props);
        this.state = {machine: props.machine || []};
    }

    render() {
        let stateEditors = this.state.machine.map(
            (state, index) => <StateEditor state={state} ident={'state' + index}
                                           onChangeName={this.changeStateName.bind(this, index)}
                                           onChangeActions={this.changeStateActions.bind(this, index)}
                                           onRemoveState={this.removeState.bind(this, index)}
            />
        );
        // <pre>{JSON.stringify(this.state.machine, null, 4)}</pre>
        return <div>
            <input name={this.props.name} type="hidden" value={JSON.stringify(this.state.machine)}/>
            {stateEditors.length === 0 ? <p className="text-muted">No states created yet</p> : ''}
            {stateEditors}
            <button type="button" className="btn btn-primary btn-sm" onClick={this.addState}>+ add state</button>
        </div>;
    }

    addState = () => {
        let newState: State = {name: "", actions: []};
        this.setState({machine: [...this.state.machine, newState]});
    }

    changeStateName(index: number, name: string) {
        this.setState({
            machine: this.state.machine.map((state, i) => i === index ? {
                name: name,
                actions: state.actions
            } : state)
        });
    }

    changeStateActions(index: number, actions: StateAction[]) {
        this.setState({
            machine: this.state.machine.map((state, i) => i === index ? {
                name: state.name,
                actions: actions
            } : state)
        });
    }

    removeState(index: number) {
        this.setState({
            machine: this.state.machine.filter((_, i) => i !== index)
        });
    }
}