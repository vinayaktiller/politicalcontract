    import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
    import api from '../../../../api';
import { c } from 'framer-motion/dist/types.d-Bq-Qm38R';

    interface BlogUser {
    id: number;
    name: string;
    profile_pic: string | null;
    relation: string;
    }

    interface Milestone {
    id: string;
    title: string;
    text: string;
    photo_url: string | null;
    type: string;
    photo_id: number | null; // <- FIX: should be number | null
    }

    interface BlogHeader {
    type: string;
    created_at: string;
    user: BlogUser;
    narrative?: string;
    }

    interface BlogBody {
    body_text: string | null;
    body_type_fields: {
        target_user?: BlogUser;
        milestone?: Milestone;
        report_kind?: string;
        time_type?: string;
        id?: string;
        level?: string;
        location?: string;
        new_users?: number;
        date?: string;
        question?: {
        id: number;
        text: string;
        rank: number;
        };
        url?: string;
        title?: string;
        contribution?: string;
        target_details?: string;
        failure_reason?: string;
        [key: string]: any;
    };
    }

    interface BlogFooter {
    likes: number[];
    relevant_count: number[];
    irrelevant_count: number[];
    shares: number[];
    comments: string[];
    has_liked: boolean;
    has_shared: boolean;
    }

    interface Comment {
    id: string;
    user: {
        id: number;
        name: string;
        profile_pic: string | null;
    };
    text: string;
    likes: number[];
    dislikes: number[];
    created_at: string;
    replies: Comment[];
    }
    interface Question {
    id: number;
    text: string;
    rank: number;
    }

    interface Answer {
    id: string;
    header: BlogHeader;
    body: BlogBody;
    footer: BlogFooter;
    comments?: Comment[];
    }

    interface AnswersState {
    question: Question | null;
    answers: Answer[];
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
    }

    const initialState: AnswersState = {
    question: null,
    answers: [],
    status: 'idle',
    error: null,
    };

    interface FetchQuestionAnswersResponse {
    question: Question;
    answers: Answer[];
    }

    // Utility to map milestone.photo_id from string|null to number|null
    function convertMilestonePhotoId(milestone: any): Milestone {
    return {
        ...milestone,
        photo_id:
        milestone.photo_id === null
            ? null
            : typeof milestone.photo_id === "string"
            ? Number(milestone.photo_id)
            : milestone.photo_id,
    };
    }

    function transformAnswers(answers: any[]): Answer[] {
    return answers.map((answer) => {
        const transformed = { ...answer };
        if (
        transformed.body &&
        transformed.body.body_type_fields &&
        transformed.body.body_type_fields.milestone
        ) {
        transformed.body.body_type_fields.milestone = convertMilestonePhotoId(
            transformed.body.body_type_fields.milestone
        );
        }
        return transformed;
    });
    }

    export const fetchQuestionAnswers = createAsyncThunk<FetchQuestionAnswersResponse, string>(
    'answers/fetchQuestionAnswers',
    async (questionId: string, { rejectWithValue }) => {
        try {
        console.log("Fetching answers for question ID:", questionId);
        const response = await api.get(`api/blog_related/question_answers/${questionId}/`);
        console.log("Raw response data:", response.data);
        // Assert response.data type before accessing its properties
        const data = response.data as FetchQuestionAnswersResponse;
        const answersTransformed = transformAnswers(data.answers);
        return {
            ...data,
            answers: answersTransformed,
        } as FetchQuestionAnswersResponse;
        } catch (err: any) {
        return rejectWithValue(err.response?.data || 'Failed to fetch answers');
        }
    }
    );

    const answersSlice = createSlice({
    name: 'answers',
    initialState,
    reducers: {
        resetAnswers: () => initialState,
    },
    extraReducers: (builder) => {
        builder
        .addCase(fetchQuestionAnswers.pending, (state) => {
            state.status = 'loading';
        })
        .addCase(fetchQuestionAnswers.fulfilled, (state, action) => {
            state.status = 'succeeded';
            state.question = action.payload.question;
            state.answers = action.payload.answers;
        })
        .addCase(fetchQuestionAnswers.rejected, (state, action) => {
            state.status = 'failed';
            state.error = action.payload as string;
        });
    },
    });

    export const { resetAnswers } = answersSlice.actions;
    export default answersSlice.reducer;
