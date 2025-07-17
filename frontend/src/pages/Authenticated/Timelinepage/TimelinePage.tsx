import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "../../../store";
import { useLocation } from "react-router-dom";
import { ArrowUp, ArrowDown } from "lucide-react";
import Profiles from "./components/Profiles";
import Bellowprofiles from "./components/Bellowprofiles";
import {
  fetchTimelineHead,
  addTimeline,
  updateScrollPosition,
  shiftTimelinePathThunk
} from "./timelineSlice";
import { ProfileData } from "./timelineTypes";

type LocationState = {
  currenttimelinenumber?: number;
  currentlineowner?: number;
};

export default function TimelinePage() {
  const dispatch = useDispatch<AppDispatch>();
  const location = useLocation();
  const state = location.state as LocationState;

  const containerRef = useRef<HTMLDivElement>(null);
  const endReached = useRef(false);
  const timelineDataRef = useRef<any>(null);

  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [boxes, setBoxes] = useState<number[]>([]);
  const [belowBoxes, setBelowBoxes] = useState<number[]>([]);
  const nextNumberRef = useRef(0);
  const boxesRef = useRef<number[]>([]);
  const [isTimelineLoading, setIsTimelineLoading] = useState(false);

  const currentTimelineNumber = state?.currenttimelinenumber ?? 1;
  const currentLineOwner = state?.currentlineowner ?? 43120704200001;

  const timelines = useSelector((s: RootState) => s.timeline.timelines);
  const timelineData = timelines[currentTimelineNumber] || {
    timelineNumber: currentTimelineNumber,
    timelineOwner: currentLineOwner,
    timelineHead: [],
    timelineTail: [],
    nextPage: 1,
    timelineHeadLength: 0,
    newload: 0,
    scrollPosition: null,
  };

  // Refs for tracking data
  useEffect(() => {
    timelineDataRef.current = timelineData;
  }, [timelineData]);

  useEffect(() => {
    boxesRef.current = boxes;
  }, [boxes]);

  // Save scroll position before unload
  useEffect(() => {
    const savePos = () => {
      if (!containerRef.current) return;
      dispatch(updateScrollPosition({
        timelineNumber: currentTimelineNumber,
        position: containerRef.current.scrollTop
      }));
    };
    
    window.addEventListener("beforeunload", savePos);
    return () => {
      savePos();
      window.removeEventListener("beforeunload", savePos);
    };
  }, [dispatch, currentTimelineNumber]);

  // Initialize timeline on mount
  useEffect(() => {
    const exists = timelines[currentTimelineNumber]?.timelineOwner === currentLineOwner;
    if (!exists) {
      dispatch(addTimeline({
        timelineNumber: currentTimelineNumber,
        timelineOwner: currentLineOwner
      }));
    }
    
    // Only fetch if we don't have data
    if (!timelineData.timelineHead.length) {
      dispatch(fetchTimelineHead({
        timelineNumber: currentTimelineNumber,
        timelineOwner: currentLineOwner
      })).finally(() => {
        setIsInitialLoad(false);
      });
    } else {
      setIsInitialLoad(false);
    }
  }, [dispatch, currentTimelineNumber, currentLineOwner]);

  // Set boxes after data loads
  useLayoutEffect(() => {
    if (isInitialLoad) return;
    
    // Initialize head boxes
    if (timelineData.timelineHead.length && boxes.length === 0) {
      nextNumberRef.current = timelineData.timelineHead.length;
      setBoxes(
        Array.from({ length: nextNumberRef.current }, 
          (_, i) => nextNumberRef.current - i)
      );
    }

    // Initialize tail boxes (in reverse order)
    if (timelineData.timelineTail.length && belowBoxes.length === 0) {
      setBelowBoxes(
        Array.from({ length: timelineData.timelineTail.length }, 
          (_, i) => timelineData.timelineTail.length - i)
      );
    }
  }, [timelineData, isInitialLoad]);

  // Restore scroll position after render
  useLayoutEffect(() => {
    if (!containerRef.current || isInitialLoad) return;
    
    if (timelineData.scrollPosition !== null) {
      // Restore saved position
      containerRef.current.scrollTop = timelineData.scrollPosition;
    } else if (boxes.length > 0 || belowBoxes.length > 0) {
      // Scroll to bottom on first load
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [timelineData.scrollPosition, isInitialLoad, boxes, belowBoxes]);

  // Handle scroll to load more
  useEffect(() => {
    const onScroll = () => {
      if (!containerRef.current || endReached.current || isTimelineLoading) return;
      
      const { scrollTop } = containerRef.current;
      const max = timelineDataRef.current.timelineHeadLength || 0;
      
      // Save current scroll position
      dispatch(updateScrollPosition({
        timelineNumber: currentTimelineNumber,
        position: scrollTop
      }));

      // Load more when near top
      if (scrollTop < 200 && timelineDataRef.current.timelineHead.length < max) {
        const oldScrollHeight = containerRef.current.scrollHeight;
        setIsTimelineLoading(true);
        
        dispatch(fetchTimelineHead({
          timelineNumber: currentTimelineNumber,
          timelineOwner: currentLineOwner
        })).then(() => {
          setIsTimelineLoading(false);
          const currentBoxes = boxesRef.current;
          const toAdd = Math.min(5, max - currentBoxes.length);
          
          if (toAdd > 0) {
            nextNumberRef.current += toAdd;
            const newBoxes = Array.from({ length: toAdd }, 
              (_, i) => nextNumberRef.current - i);
            
            setBoxes(prev => [...newBoxes, ...prev]);
            
            // Adjust scroll position after adding new items
            setTimeout(() => {
              if (containerRef.current) {
                const newScrollHeight = containerRef.current.scrollHeight;
                containerRef.current.scrollTop = newScrollHeight - oldScrollHeight;
              }
            }, 0);
          } else {
            endReached.current = true;
          }
        });
      }
    };

    containerRef.current?.addEventListener("scroll", onScroll);
    return () => {
      containerRef.current?.removeEventListener("scroll", onScroll);
    };
  }, [dispatch, currentTimelineNumber, currentLineOwner, isTimelineLoading]);

  const getScrollPosition = () => containerRef.current?.scrollTop ?? 0;
  
  const handleShift = (profileId: number, idx: number) => {
    dispatch(shiftTimelinePathThunk({
      timelineNumber: currentTimelineNumber,
      profileId,
      index: idx
    }));
  };

  return (
    <div ref={containerRef} className="dynamic-boxes-container">
      {/* Timeline Head */}
      {boxes.map((num, i) => {
        const pd = timelineData.timelineHead[num - 1] as ProfileData;
        const isOrigin = num === boxes.length;
        return (
          <div key={`head-${num}`} className="dynamic-boxes-box-container">
            {i > 0 && <ArrowUp className="dynamic-boxes-arrow" />}
            <Profiles
              parentNumber={num}
              profileData={{ ...pd, ...(isOrigin ? { origin: true } : {}) }}
              getScrollPosition={getScrollPosition}
              timelineNumber={currentTimelineNumber}
            />
          </div>
        );
      })}

      {/* Timeline Tail */}
      {belowBoxes.map((num, idx) => {
        const pd = timelineData.timelineTail[idx] as ProfileData;
        const isEndPoint = idx === timelineData.timelineTail.length - 1;

        return (
          <div key={`tail-${num}`} className="dynamic-boxes-box-container">
            <ArrowDown className="dynamic-boxes-arrow" />
            <div className="dynamic-boxes-row">
              <Bellowprofiles
                parentNumber={idx}
                last={timelineData.timelineTail.length}
                isEndPoint={isEndPoint}
                profileData={pd}
                getScrollPosition={getScrollPosition}
                timelineNumber={currentTimelineNumber}
                onShiftPath={id => handleShift(id, idx)}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}